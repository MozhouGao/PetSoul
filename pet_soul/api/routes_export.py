"""
Export routes — generate Unity-ready bundles.
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from pet_soul.config import CONFIG
from pet_soul.db.auth import get_user_id
from pet_soul.db.supabase_client import get_supabase
from pet_soul.runtime_export.unity_exporter import export_to_unity, export_to_zip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/{pet_id}/unity")
def export_pet_unity(pet_id: int, user_id: str = Depends(get_user_id)):
    """Generate a Unity-ready export bundle for a pet and return as ZIP.

    Bundles the 3D mesh, personality profile, and motion data into a
    single downloadable archive.
    """
    sb = get_supabase()

    # Fetch pet
    pet_resp = (
        sb.table("pets")
        .select("*")
        .eq("id", pet_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if pet_resp.data is None:
        raise HTTPException(status_code=404, detail="Pet not found")

    pet = pet_resp.data
    mesh_path = None
    if pet.get("model_filename"):
        candidate = CONFIG.models_dir / pet["model_filename"]
        if candidate.exists():
            mesh_path = str(candidate)

    # Fetch latest personality
    personality = None
    pers_resp = (
        sb.table("personality_profiles")
        .select("vector")
        .eq("pet_id", pet_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if pers_resp.data:
        personality = pers_resp.data[0].get("vector")

    # Fetch latest motion stats
    motion_stats = None
    motion_resp = (
        sb.table("motion_data")
        .select("stats")
        .eq("pet_id", pet_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if motion_resp.data:
        motion_stats = motion_resp.data[0].get("stats")

    # Build export
    with tempfile.TemporaryDirectory() as tmp_dir:
        bundle_dir = Path(tmp_dir) / f"pet_{pet_id}_unity"
        export_to_unity(
            output_dir=str(bundle_dir),
            mesh_path=mesh_path,
            personality=personality,
            motion_stats=motion_stats,
            metadata={
                "pet_id": pet_id,
                "name": pet.get("name", ""),
                "species": pet.get("species", "dog"),
                "breed": pet.get("breed", ""),
            },
        )

        zip_path = Path(tmp_dir) / f"pet_{pet_id}_unity.zip"
        export_to_zip(str(bundle_dir), str(zip_path))

        # Move zip to models dir for serving
        final_zip = CONFIG.models_dir / f"pet_{pet_id}_unity.zip"
        zip_path.rename(final_zip)

    return FileResponse(
        path=str(final_zip),
        filename=f"pet_{pet_id}_unity.zip",
        media_type="application/zip",
    )
