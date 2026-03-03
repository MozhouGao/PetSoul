# CLAUDE.md — Pet Soul Project Guide

## Project Overview

Pet Soul is a **Pet Digital Twin Platform** that converts pet photographs and videos into interactive 3D companions with personality and behavior. Users upload photos/videos, the system detects the pet, extracts appearance + motion + audio traits, generates a 3D mesh, and packages everything for a Unity runtime.

**Version**: v3.0 (Full Digital Twin)
**Branch**: `v0.1` (main branch: `main`)
**Python**: 3.10+ (tested on 3.10.14)
**Platform**: Tested on Windows/WSL2, Apple M2 compatible

## Architecture

Two-branch pipeline:

```
Appearance Branch:  Photo → YOLO → CLIP → Meshy API → 3D GLB Model
Behavior Branch:    Video → MediaPipe → 3D Lift → Motion AE → Personality → FSM
                    Audio → MFCC → CNN → Vocal/Emotion Classification
World Model (v3):   Latent State → Dynamics Model → Policy Network → Autonomous Behavior

Both branches → Unity Export Bundle → Interactive AI Pet
```

## Key Files

| File | Purpose |
|---|---|
| `pet_soul/main.py` | Entry point — starts uvicorn server |
| **API** | |
| `pet_soul/api/app.py` | FastAPI server, CORS, route registration |
| `pet_soul/api/routes_auth.py` | Auth0 endpoints (config, me, sync) |
| `pet_soul/api/routes_pets.py` | Pet CRUD + 3D generation (Supabase) |
| `pet_soul/api/routes_motion.py` | Video/audio upload + motion analysis |
| `pet_soul/api/routes_export.py` | Unity export bundle generation |
| **Appearance** | |
| `pet_soul/appearance/pipeline.py` | Orchestrator — detection → extraction → 3D |
| `pet_soul/appearance/pet_detector.py` | YOLOv8 Nano detection |
| `pet_soul/appearance/attribute_extractor.py` | CLIP zero-shot classification |
| `pet_soul/appearance/prompt_builder.py` | PetProfile → texture prompt |
| `pet_soul/appearance/meshy_generator.py` | Meshy.ai API client |
| `pet_soul/appearance/pet_profile.py` | PetProfile dataclass |
| **Motion** | |
| `pet_soul/motion/pose_extractor.py` | MediaPipe 2D keypoint extraction |
| `pet_soul/motion/lift_2d_to_3d.py` | MLP 2D→3D pose lifting |
| `pet_soul/motion/motion_autoencoder.py` | LSTM VAE for motion style |
| `pet_soul/motion/motion_features.py` | Handcrafted motion statistics |
| **Behavior** | |
| `pet_soul/behavior/state_machine.py` | FSM (Idle/Curious/Playful/Alert/Resting) |
| `pet_soul/behavior/personality.py` | PersonalityProfile from motion+audio |
| **Audio** | |
| `pet_soul/audio/feature_extractor.py` | MFCC + audio statistics |
| `pet_soul/audio/audio_classifier.py` | CNN vocal/emotion classifier |
| **World Model** | |
| `pet_soul/world_model/latent_dynamics.py` | Latent state transition predictor |
| `pet_soul/world_model/policy_network.py` | Action selection via imagination |
| **Runtime Export** | |
| `pet_soul/runtime_export/unity_exporter.py` | Unity bundle packaging |
| **Config & DB** | |
| `pet_soul/config/settings.py` | Config dataclass + PROJECT_ROOT |
| `pet_soul/db/supabase_client.py` | Supabase client (replaces SQLAlchemy) |
| `pet_soul/db/auth.py` | Auth0 JWT verification |

## Directory Structure

```
PetSoul/
├── pet_soul/                            # Main Python package
│   ├── __init__.py                      # Version: 3.0.0
│   ├── main.py                          # Entry point
│   ├── config/                          # Configuration
│   │   └── settings.py                  # Config dataclass + PROJECT_ROOT
│   ├── appearance/                      # ML pipeline (photo → 3D)
│   │   ├── pipeline.py, pet_detector.py, attribute_extractor.py
│   │   ├── prompt_builder.py, meshy_generator.py, pet_profile.py
│   ├── motion/                          # Video → motion (v2.1)
│   │   ├── pose_extractor.py            # MediaPipe
│   │   ├── lift_2d_to_3d.py             # MLP lifter
│   │   ├── motion_autoencoder.py        # LSTM VAE
│   │   └── motion_features.py           # Motion statistics
│   ├── behavior/                        # Behavior engine (v2.2)
│   │   ├── state_machine.py             # FSM
│   │   └── personality.py               # Personality profile
│   ├── audio/                           # Audio analysis (v2.2)
│   │   ├── feature_extractor.py         # MFCC
│   │   └── audio_classifier.py          # CNN classifier
│   ├── world_model/                     # World model (v3.0)
│   │   ├── latent_dynamics.py           # State predictor
│   │   └── policy_network.py            # Action selection
│   ├── runtime_export/                  # Unity export
│   │   └── unity_exporter.py
│   ├── db/                              # Database layer
│   │   ├── supabase_client.py           # Supabase client
│   │   └── auth.py                      # Auth0 JWT verification
│   └── api/                             # FastAPI endpoints
│       ├── app.py, routes_auth.py, routes_pets.py
│       ├── routes_motion.py, routes_export.py
├── tests/
│   └── test_quick.py
├── requirements.txt
├── .env.example
├── yolov8n.pt
├── static/, models/, frontend/, docs/
└── CLAUDE.md
```

## Tech Stack

- **Web Framework**: FastAPI + Uvicorn
- **Auth**: Auth0 (JWT RS256 verification)
- **Database**: Supabase (PostgreSQL)
- **Detection**: YOLOv8 Nano
- **Classification**: CLIP ViT-base-32
- **3D Generation**: Meshy.ai cloud API (meshy-6)
- **Pose Extraction**: MediaPipe
- **Motion Learning**: PyTorch LSTM VAE
- **Audio**: librosa MFCC + PyTorch CNN
- **Deep Learning**: PyTorch, Transformers, Accelerate
- **Runtime**: Unity (export bundles)

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Server status |
| `GET` | `/health` | No | Component readiness |
| `GET` | `/test` | No | Web test UI redirect |
| `POST` | `/generate-3d-model` | No | Quick 3D generation |
| `GET` | `/auth/config` | No | Auth0 config for frontend |
| `GET` | `/auth/me` | Yes | Current user from token |
| `POST` | `/auth/sync` | Yes | Sync Auth0 user to Supabase |
| `GET` | `/pets` | Yes | List user's pets |
| `POST` | `/pets` | Yes | Create pet + generate 3D |
| `GET` | `/pets/{id}` | Yes | Get pet details |
| `DELETE` | `/pets/{id}` | Yes | Delete pet |
| `POST` | `/motion/analyze-video` | Yes | Extract motion + personality |
| `POST` | `/motion/analyze-audio` | Yes | Classify pet vocalisations |
| `GET` | `/motion/personality/{pet_id}` | Yes | Get personality profile |
| `POST` | `/export/{pet_id}/unity` | Yes | Download Unity export ZIP |

## Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Then fill in your keys
python -m pet_soul.main
```

Required environment variables (see `.env.example`):
- `MESHY_API_KEY` — Meshy.ai Pro account
- `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `AUTH0_CLIENT_ID` — Auth0 tenant
- `SUPABASE_URL`, `SUPABASE_KEY` — Supabase project

## Development Commands

```bash
# Run the server
python -m pet_soul.main

# Quick CLI test (requires server running)
python tests/test_quick.py <image_path>

# Test via curl
curl http://localhost:8000/health
curl -X POST http://localhost:8000/generate-3d-model -F "file=@photo.jpg"
```

## Coding Conventions

- Python dataclasses for data models (not Pydantic, except API request/response schemas)
- Frozen dataclass for configuration (`Config`)
- Standard library `logging` (no third-party logger)
- Type hints used throughout
- All file paths use `pathlib.Path`
- Imports are absolute package imports (e.g., `from pet_soul.config import CONFIG`)
- Auth via Auth0 JWT verification (no passwords stored server-side)
- Data via Supabase client (no local ORM)

## Important Notes

- `.env` contains API keys — never commit this file
- `yolov8n.pt` is committed to the repo (6.5MB)
- CLIP model auto-downloads on first run (~300MB to HuggingFace cache)
- 3D generation takes 1–3 minutes per model via Meshy.ai
- Motion/audio models require training on pet-specific data before production use
- World model (v3.0) modules are architecturally complete but require training
