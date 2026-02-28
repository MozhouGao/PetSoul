"""
FastAPI Backend Application
Pet 3D Model Generator API
"""

import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import cv2
import numpy as np
from PIL import Image
import io
from pathlib import Path
import uuid
import time

from config import CONFIG
from pipeline import Pet3DModelPipeline
from database import init_db
from routes_auth import router as auth_router
from routes_pets import router as pets_router, set_pipeline

logger = logging.getLogger(__name__)

app = FastAPI(title="Pet 3D Model Generator API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = Pet3DModelPipeline(
    use_clip=True,
    output_format=CONFIG.default_output_format
)

# Share pipeline with pets router
set_pipeline(pipeline)

# Include routers
app.include_router(auth_router)
app.include_router(pets_router)

# Web test page
if CONFIG.static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(CONFIG.static_dir)), name="static")

# Output directory for 3D models
CONFIG.models_dir.mkdir(exist_ok=True)
if CONFIG.models_dir.exists():
    app.mount("/models", StaticFiles(directory=str(CONFIG.models_dir)), name="models")

# Serve React production build if it exists
if CONFIG.frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(CONFIG.frontend_dist / "assets")), name="frontend-assets")


def api_error(status_code: int, message: str):
    """Raise a consistent API error response."""
    raise HTTPException(status_code=status_code, detail={"success": False, "error": message})


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
async def root():
    # Serve React index.html if production build exists
    index = CONFIG.frontend_dist / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {
        "message": "Pet 3D Model Generator API",
        "status": "running",
        "pipeline_ready": pipeline.is_ready(),
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "pipeline_ready": pipeline.is_ready(),
        "detector_ready": pipeline.detector.is_ready(),
        "generator_ready": pipeline.generator.is_ready()
    }


@app.get("/test")
async def web_test_page():
    """Redirect to browser test page"""
    return RedirectResponse(url="/static/test.html")


@app.post("/generate-3d-model")
async def generate_3d_model(
    file: UploadFile = File(...),
):
    """
    Generate 3D model from pet photo.

    Returns JSON with pet profile, texture prompt, and a download link
    for the generated GLB model.
    """
    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            api_error(400, "File must be an image")

        # Read and decode image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_array = np.array(image)

        if len(image_array.shape) != 3 or image_array.shape[2] not in (3, 4):
            api_error(400, "Invalid image format")

        # Convert RGBA to RGB if needed
        if image_array.shape[2] == 4:
            image_rgb = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
        else:
            image_rgb = image_array

        # Generate unique filename
        model_id = f"pet_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        output_filename = f"{model_id}.glb"
        output_path = CONFIG.models_dir / output_filename

        # Process through pipeline
        result = pipeline.process(
            image_rgb,
            output_path=str(output_path),
        )

        if "error" in result:
            api_error(500, result["error"])

        model_path = result.get("model_path")
        if not model_path or not Path(model_path).exists():
            api_error(500, "Failed to generate 3D model")

        return {
            "success": True,
            "profile": result.get("profile", {}),
            "texture_prompt": result.get("prompt", ""),
            "model_url": f"/models/{output_filename}",
            "filename": output_filename,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error generating 3D model")
        api_error(500, f"Error generating 3D model: {str(e)}")


# SPA catch-all — must be last
@app.get("/{path:path}")
async def spa_catch_all(path: str):
    index = CONFIG.frontend_dist / "index.html"
    if index.exists():
        return FileResponse(str(index))
    raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    uvicorn.run(app, host=CONFIG.host, port=CONFIG.port)
