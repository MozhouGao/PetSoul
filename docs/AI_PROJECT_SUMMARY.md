# AI Project Summary — Pet Soul

> This file is designed for GenAI tools and LLMs. Read this file first to understand the entire project without scanning source code. For deeper detail, refer to the linked docs.

---

## What Is This Project?

**Pet Soul** is a Python backend that turns a pet photograph into a textured 3D model. Upload a photo of a dog or cat, and the system detects the pet, identifies its breed and physical traits, then generates a downloadable 3D mesh (GLB/OBJ/PLY/STL).

---

## How It Works (Pipeline)

```
Photo (JPEG/PNG)
  → [YOLOv8] Detect pet, crop bounding box
  → [CLIP]   Extract breed, coat colors, markings, physical attributes
  → [PetProfile] Store all attributes in a dataclass
  → [PromptBuilder] Build a natural-language texture prompt
  → [Meshy.ai API] Send cropped image + prompt → receive 3D model
  → Save GLB file → Return to user
```

**Total processing time:** 1–3 minutes (dominated by Meshy.ai cloud generation).

---

## Tech Stack (Quick Reference)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Web API | FastAPI + Uvicorn | REST endpoints, file uploads, CORS |
| Pet Detection | YOLOv8 Nano | COCO classes 15 (dog) and 16 (cat) |
| Attribute Extraction | OpenAI CLIP (ViT-base-32) | Zero-shot classification |
| 3D Generation | Meshy.ai API (cloud) | Requires `MESHY_API_KEY` env var |
| Language | Python 3.10.14 | PyTorch 2.1, Transformers 4.35 |

---

## File Map

| File | Role |
|------|------|
| `app.py` | FastAPI server — defines all API endpoints |
| `pipeline.py` | Orchestrator — connects detector → extractor → prompt → generator |
| `pet_detector.py` | YOLOv8 wrapper — detects pets, returns bounding box and crop |
| `attribute_extractor.py` | CLIP wrapper — extracts breed (25), colors (15), markings (9), 6 physical traits |
| `prompt_builder.py` | Converts PetProfile into a texture prompt string |
| `meshy_generator.py` | Meshy.ai API client — submit task, poll status, download GLB |
| `pet_profile.py` | `PetProfile` dataclass — structured pet attribute storage |
| `config.py` | All settings: paths, thresholds, model names, API config, server host/port |
| `breed_data.py` | Body proportion parameters for 25 dog breeds (used by procedural fallback) |
| `procedural_generator.py` | CPU-only fallback — builds mesh from geometric primitives (no API needed) |
| `model3d_generator.py` | TripoSR integration (deprecated, kept for reference) |
| `quick_test.py` | CLI test script — health check, analyze, generate |
| `static/test.html` | Browser test UI served at `/test` |

---

## API Endpoints

| Method | Path | Purpose | Input | Output |
|--------|------|---------|-------|--------|
| GET | `/` | Server status | — | JSON |
| GET | `/health` | Component readiness | — | JSON |
| GET | `/test` | Web test UI | — | HTML redirect |
| POST | `/analyze-pet` | Detect + extract attributes | Image file | JSON profile |
| POST | `/generate-3d-model` | Full pipeline → 3D model | Image + format | Binary 3D file |
| POST | `/generate-avatar` | Legacy alias | Image + style | Binary 3D file |

---

## Data Model: PetProfile

```
PetProfile:
  species: str           # "dog" or "cat"
  breed: str             # e.g. "Siberian Husky"
  breed_confidence: float
  coat_colors: list[str] # e.g. ["black", "white"]
  markings: list[str]    # e.g. ["facial mask"]
  fur_length: str        # short | medium | long | wire-haired
  body_type: str         # compact | athletic | stocky | slender | large
  ear_shape: str         # floppy | erect | semi-erect | rose | button
  tail_type: str         # long_curved | long_straight | curled | short | docked
  snout_length: str      # flat | short | medium | long
  size_class: str        # toy | small | medium | large | giant
  leg_length: str        # short | medium | long
```

---

## Configuration (config.py)

| Setting | Value | Purpose |
|---------|-------|---------|
| `yolo_model` | `yolov8n.pt` | Detection model file |
| `clip_model_name` | `openai/clip-vit-base-patch32` | CLIP model ID |
| `yolo_conf_threshold` | 0.25 | Minimum detection confidence |
| `coat_color_threshold` | 0.05 | Minimum CLIP score for colors |
| `marking_threshold` | 0.15 | Minimum CLIP score for markings |
| `meshy_ai_model` | `meshy-6` | Meshy.ai generation model |
| `meshy_target_polycount` | 30,000 | Triangle count target |
| `meshy_timeout` | 300s | Max wait for generation |
| `host` / `port` | 0.0.0.0:8000 | Server binding |

---

## Environment Requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.9–3.11 (project pins 3.10.14) |
| `MESHY_API_KEY` | Required env var — from meshy.ai Pro account (~$20/month) |
| `yolov8n.pt` | Must exist in project root (~6.5MB, in repo) |
| CLIP weights | ~300MB, auto-downloaded on first run to `~/.cache/huggingface/` |
| RAM | Minimum 4GB (CLIP + YOLOv8 use ~1–2GB) |
| GPU | Not required — CPU inference works, Meshy.ai handles 3D generation in cloud |

---

## Project Status & Roadmap

**Current state:** MVP (v0.1 branch)

| Feature | Status |
|---------|--------|
| Pet detection (dogs + cats) | Working |
| Breed classification (25 dog breeds) | Working |
| Attribute extraction (colors, markings, physical) | Working |
| 3D generation via Meshy.ai | Working |
| Web test UI | Working |
| Procedural fallback (CPU mesh) | Available but basic |
| LoRA avatar generation | Files present, not integrated |
| Cat breed support | Not implemented |
| Mobile frontend | Not included |
| TripoSR local generation | Deprecated |

---

## Key Dependencies (requirements.txt)

```
fastapi==0.104.1          # Web framework
uvicorn[standard]==0.24.0 # ASGI server
ultralytics==8.0.196      # YOLOv8
torch==2.1.0              # PyTorch
transformers==4.35.0      # CLIP model loading
pillow==10.1.0            # Image processing
opencv-python==4.8.1.78   # Computer vision
requests>=2.31.0          # Meshy.ai HTTP client
python-dotenv==1.0.0      # .env file loading
numpy>=1.23.0,<1.25.0     # Array operations
scipy==1.11.4             # Scientific computing
accelerate==0.24.1        # Model loading
safetensors>=0.4.0        # Weight serialization
aiofiles==23.2.1          # Async file I/O
python-multipart==0.0.6   # File upload parsing
```

**Optional (commented out):** `pymeshlab` (mesh processing), `rembg` (background removal)

---

## Documentation Index

| File | Contents |
|------|----------|
| `docs/AI_PROJECT_SUMMARY.md` | **This file** — complete project overview for AI/LLM consumption |
| `docs/tech_stack.md` | Detailed technology and dependency breakdown |
| `docs/architecture.md` | System diagram, component responsibilities, data flow |
| `docs/api_reference.md` | Full API documentation with request/response examples |
| `docs/skills_required.md` | Technical skills needed to work on this project |
| `docs/project_structure.md` | Directory tree with file descriptions |
| `docs/development_guide.md` | Setup, testing, troubleshooting, and environment config |
| `docs/additional_notes.md` | Gaps, Windows support, model weights, costs, optional deps |
| `README.md` | User-facing project overview (root) |
| `REFACTOR_LOG.md` | TripoSR → Meshy.ai migration history |
| `LORA_SETUP.md` | LoRA configuration guide for avatar generation |
