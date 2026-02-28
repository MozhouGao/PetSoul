# CLAUDE.md — Pet Soul Project Guide

## Project Overview

Pet Soul converts pet photographs into textured 3D models (GLB/OBJ). Users upload a photo of a dog or cat, the system detects the pet, classifies breed and physical attributes, then generates a downloadable 3D mesh via the Meshy.ai cloud API.

**Version**: v0.1 (MVP)
**Branch**: `v0.1` (main branch: `main`)
**Python**: 3.10.14 (compatible with 3.9–3.11)
**Platform**: Tested on Windows/WSL2

## Architecture

Three-layer design:

1. **Python Backend** (FastAPI) — detection, extraction, prompt building, API orchestration
2. **Meshy.ai Cloud** — 3D model generation (no local GPU required)
3. **iOS App** (Unity, planned/not implemented) — photo capture and 3D viewing

### Pipeline Flow

```
Photo → YOLOv8 Detection → CLIP Attribute Extraction → PetProfile → Prompt Builder → Meshy.ai API → GLB File
```

## Key Files

| File | Purpose |
|---|---|
| `app.py` | FastAPI server, API endpoints, CORS setup |
| `pipeline.py` | Orchestrator — coordinates all components |
| `pet_detector.py` | YOLOv8 Nano wrapper for dog/cat detection |
| `attribute_extractor.py` | CLIP zero-shot classification (breed, coat, markings, body) |
| `prompt_builder.py` | Converts PetProfile into natural-language texture prompt |
| `meshy_generator.py` | Meshy.ai REST API client (polling-based async) |
| `pet_profile.py` | `PetProfile` dataclass — structured attribute container |
| `config.py` | `Config` frozen dataclass — all thresholds, paths, model names |
| `quick_test.py` | CLI test script for running pipeline without server |
| `static/test.html` | Browser-based test UI |

## Directory Structure

```
pet_soul/
├── app.py, pipeline.py, config.py      # Core backend
├── pet_detector.py                      # YOLOv8 detection
├── attribute_extractor.py               # CLIP classification
├── prompt_builder.py                    # Texture prompt generation
├── meshy_generator.py                   # Meshy.ai API client
├── pet_profile.py                       # Data model
├── quick_test.py                        # CLI test
├── requirements.txt                     # Pinned dependencies
├── .env                                 # MESHY_API_KEY (not committed)
├── yolov8n.pt                           # YOLOv8 Nano weights (6.5MB)
├── loras/pet_cartoon_lora.safetensors   # LoRA weights (future use)
├── static/                              # Web test UI
├── models/                              # Generated 3D output files
├── avatars/                             # Generated avatar output
├── docs/                                # 10 markdown docs (see below)
├── PetSoulApp/                          # Unity iOS app (planned)
├── TripoSR/                             # Deprecated local 3D gen
└── CLAUDE.md                            # This file
```

## Tech Stack

- **Web Framework**: FastAPI 0.104.1 + Uvicorn 0.24.0
- **Detection**: Ultralytics YOLOv8 Nano (`yolov8n.pt`, 6.5MB)
- **Classification**: OpenAI CLIP ViT-base-32 (`openai/clip-vit-base-patch32`, ~300MB, auto-downloaded)
- **3D Generation**: Meshy.ai cloud API (model: `meshy-6`, 15k–30k polygons)
- **Deep Learning**: PyTorch 2.1.0, Transformers 4.35.0, Accelerate 0.24.1
- **Image Processing**: Pillow 10.1.0, OpenCV 4.8.1
- **Utilities**: NumPy, SciPy, Requests, aiofiles, python-dotenv

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Server status + capabilities |
| `GET` | `/health` | Component readiness check |
| `GET` | `/test` | Redirects to web test UI |
| `POST` | `/analyze-pet` | Detection + attribute extraction → JSON profile |
| `POST` | `/generate-3d-model` | Full pipeline → binary 3D file (profile in headers) |
| `POST` | `/generate-avatar` | Legacy alias for `/generate-3d-model` |
| `GET` | `/models/<file>.glb` | Serve generated 3D model files |

## Data Model — PetProfile

```python
@dataclass
class PetProfile:
    species: str              # "dog" or "cat"
    breed: Optional[str]
    breed_confidence: float
    coat_colors: List[str]    # up to 3, threshold 0.05
    markings: List[str]       # threshold 0.15
    fur_length: Optional[str]
    body_type: Optional[str]  # compact, athletic, stocky, slender, large
    ear_shape: Optional[str]  # floppy, erect, semi_erect, rose, button
    tail_type: Optional[str]  # long_curved, long_straight, curled, short, docked
    snout_length: Optional[str]  # flat, short, medium, long
    size_class: Optional[str]    # toy, small, medium, large, giant
    leg_length: Optional[str]    # short, medium, long
```

## Configuration (config.py)

All settings live in a frozen `Config` dataclass. Key values:

- `yolo_conf_threshold`: 0.25
- `coat_color_threshold`: 0.05, `marking_threshold`: 0.15, `max_coat_colors`: 3
- `clip_model_name`: `openai/clip-vit-base-patch32`
- `meshy_ai_model`: `meshy-6`, `meshy_target_polycount`: 15000
- `meshy_poll_interval`: 5.0s, `meshy_timeout`: 300.0s
- `default_output_format`: `glb`
- Server: `0.0.0.0:8000`

## Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/WSL
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
echo "MESHY_API_KEY=your_key" > .env
python app.py                    # Runs on http://localhost:8000
```

- Requires **Meshy.ai Pro** account (~$20/month for ~50 models)
- `MESHY_API_KEY` must be set in `.env`
- Minimum 4GB RAM (CLIP + YOLOv8 use ~1–2GB)
- No GPU required — CPU inference works; Meshy handles 3D in cloud

## Development Commands

```bash
# Run the server
python app.py

# Quick CLI test (no server needed)
python quick_test.py

# Test via curl
curl -X POST http://localhost:8000/analyze-pet -F "file=@photo.jpg"
curl -X POST http://localhost:8000/generate-3d-model -F "file=@photo.jpg" --output model.glb
```

## Current Status & Known Gaps

### Working
- Dog detection and classification (25 breeds)
- Coat color (15 options), markings (9 options), physical trait extraction
- 3D model generation via Meshy.ai
- Web test UI at `/test`

### Not Implemented
- Cat breed classification (detection works, breeds not classified)
- LoRA-based avatar generation (weights present but not wired in)
- Unity iOS app (plan documented in `docs/MOBILE_APP_PLAN.md`)
- TripoSR local generation (deprecated, replaced by Meshy.ai)

## Documentation Index (docs/)

| File | Content |
|---|---|
| `AI_PROJECT_SUMMARY.md` | Best single-file overview for LLMs |
| `FULL_ARCHITECTURE.md` | System architecture with network diagrams |
| `tech_stack.md` | Detailed technology breakdown |
| `architecture.md` | Component responsibilities and data flow |
| `api_reference.md` | Full API docs with request/response examples |
| `project_structure.md` | Directory tree and file descriptions |
| `development_guide.md` | Setup, testing, troubleshooting |
| `skills_required.md` | Required technical knowledge |
| `additional_notes.md` | Gaps, costs, optional dependencies |
| `MOBILE_APP_PLAN.md` | iOS app implementation plan (Unity) |

## Coding Conventions

- Python dataclasses for data models (not Pydantic)
- Frozen dataclass for configuration (`Config`)
- Standard library `logging` (no third-party logger)
- Type hints used throughout
- Async not used in pipeline (sync requests to Meshy.ai with polling)
- FastAPI handles async at the endpoint level
- All file paths use `pathlib.Path`
- Imports are absolute (no relative imports)

## Important Notes

- `.env` contains `MESHY_API_KEY` — never commit this file
- `yolov8n.pt` is committed to the repo (6.5MB)
- CLIP model auto-downloads on first run (~300MB to HuggingFace cache)
- 3D generation takes 1–3 minutes per model via Meshy.ai
- Output files are 15–30MB GLB files stored in `models/`
- `install.bat` provided for Windows setup
