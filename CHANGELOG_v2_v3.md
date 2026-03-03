# PetSoul Changelog — v1.0 → v3.0

## Summary

PetSoul was refactored from a flat, single-directory Python project (v1.0) into a fully modularized Python package (v2.0), then extended with motion capture, behavior AI, audio classification, runtime export, and a world model to become a complete Pet Digital Twin Platform (v3.0). Authentication was migrated from local bcrypt/JWT to **Auth0**, and the database was migrated from SQLite/SQLAlchemy to **Supabase** (PostgreSQL).

---

## Step 1 — v2.0: Codebase Modularization

**Goal:** Restructure the flat project root into a proper `pet_soul/` Python package with logical submodules.

### What changed

- Created the `pet_soul/` package with four submodules:
  - `pet_soul/config/` — centralized configuration
  - `pet_soul/appearance/` — detection, extraction, prompt building, 3D generation
  - `pet_soul/db/` — database and authentication
  - `pet_soul/api/` — FastAPI application and route handlers

- Moved 14 Python files from the project root into the package:

  | Old Location (root) | New Location |
  |---|---|
  | `config.py` | `pet_soul/config/settings.py` |
  | `pet_profile.py` | `pet_soul/appearance/pet_profile.py` |
  | `pet_detector.py` | `pet_soul/appearance/pet_detector.py` |
  | `attribute_extractor.py` | `pet_soul/appearance/attribute_extractor.py` |
  | `prompt_builder.py` | `pet_soul/appearance/prompt_builder.py` |
  | `meshy_generator.py` | `pet_soul/appearance/meshy_generator.py` |
  | `pipeline.py` | `pet_soul/appearance/pipeline.py` |
  | `database.py` | `pet_soul/db/database.py` |
  | `db_models.py` | `pet_soul/db/models.py` |
  | `auth.py` | `pet_soul/db/auth.py` |
  | `app.py` | `pet_soul/api/app.py` |
  | `routes_auth.py` | `pet_soul/api/routes_auth.py` |
  | `routes_pets.py` | `pet_soul/api/routes_pets.py` |
  | `quick_test.py` | `tests/test_quick.py` |

- Introduced `PROJECT_ROOT` in `pet_soul/config/settings.py` to anchor all file paths correctly after the move (`Path(__file__).resolve().parent.parent.parent`).

- Fixed YOLO model path in `pet_detector.py` to use `PROJECT_ROOT / CONFIG.yolo_model` instead of `Path(__file__).parent`.

- Updated all imports across every file from flat (`from config import CONFIG`) to package-qualified (`from pet_soul.config import CONFIG`).

- Created `pet_soul/main.py` as the new entry point (replaces `python app.py` with `python -m pet_soul.main`).

- Deleted all old `.py` files from the project root.

---

## Step 2 — Auth0 Integration

**Goal:** Replace local password-based authentication (bcrypt + self-signed JWT) with Auth0 token verification.

### What changed

- **Rewrote `pet_soul/db/auth.py`:**
  - Removed `hash_password()`, `verify_password()`, `create_access_token()` functions
  - Added `verify_token()` using `jwt.PyJWKClient` to fetch RS256 signing keys from Auth0's JWKS endpoint
  - Added `get_current_user()` and `get_user_id()` FastAPI dependencies
  - Token validation checks: signature (RS256), audience, issuer, expiration

- **Rewrote `pet_soul/api/routes_auth.py`:**
  - Removed `/auth/register` and `/auth/login` (password-based) endpoints
  - Added `GET /auth/config` — returns Auth0 domain/clientId/audience for frontend SDK initialization
  - Added `GET /auth/me` — returns decoded token payload for the authenticated user
  - Added `POST /auth/sync` — upserts Auth0 user profile into Supabase `users` table

- **Updated `pet_soul/config/settings.py`:**
  - Added `auth0_domain`, `auth0_audience`, `auth0_client_id` fields (read from environment)

- **Updated `.env.example`:**
  - Added `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `AUTH0_CLIENT_ID` variables

- **Removed dependencies:** `passlib[bcrypt]`, `bcrypt`
- **Added dependencies:** `PyJWT[crypto]>=2.8.0`, `cryptography>=41.0.0`

---

## Step 3 — Supabase Integration

**Goal:** Replace SQLite + SQLAlchemy ORM with Supabase (hosted PostgreSQL) using the `supabase-py` client.

### What changed

- **Created `pet_soul/db/supabase_client.py`:**
  - Lazy-initialized Supabase client via `get_supabase()`
  - `is_supabase_ready()` health check
  - Documented required SQL schema for `users`, `pets`, `motion_data`, `personality_profiles` tables

- **Deleted `pet_soul/db/database.py`** (SQLAlchemy engine, `init_db()`, `get_db()`)
- **Deleted `pet_soul/db/models.py`** (SQLAlchemy ORM models for `User`, `Pet`)

- **Rewrote `pet_soul/api/routes_pets.py`:**
  - All CRUD operations now use `get_supabase().table("pets").select/insert/update/delete`
  - Returns dict responses instead of ORM objects
  - Uses `get_user_id` dependency (Auth0 `sub` claim) for ownership filtering

- **Updated `pet_soul/api/app.py`:**
  - Removed `init_db()` call on startup
  - Added `is_supabase_ready()` to health check endpoint
  - Imported and wired Supabase readiness check

- **Updated `pet_soul/config/settings.py`:**
  - Added `supabase_url`, `supabase_key` fields (read from environment)
  - Removed `db_path` field (SQLite no longer used)

- **Updated `pet_soul/db/__init__.py`:**
  - Exports `get_supabase`, `is_supabase_ready` instead of `init_db`, `get_db`, `User`, `Pet`

- **Removed dependencies:** `SQLAlchemy`
- **Added dependencies:** `supabase>=2.0.0`

---

## Step 4 — v2.1: Motion Module

**Goal:** Extract motion data from pet video clips for personality inference and animation.

### New files

- **`pet_soul/motion/pose_extractor.py`**
  - MediaPipe-based 2D keypoint extraction from video frames
  - Defines 14 pet keypoint names (nose, ears, shoulders, hips, paws, tail)
  - Maps human MediaPipe landmarks to pet anatomy
  - Methods: `extract_from_frame()`, `extract_from_video()`

- **`pet_soul/motion/lift_2d_to_3d.py`**
  - `PoseLifter` — 3-layer MLP that predicts depth (z) from 2D (x, y) keypoints
  - `lift_sequence()` — lifts a full time-series of 2D poses to 3D
  - `smooth_trajectory()` — Savitzky-Golay temporal smoothing to reduce jitter

- **`pet_soul/motion/motion_autoencoder.py`**
  - `MotionEncoder` — LSTM encoder producing mean/logvar (VAE latent space)
  - `MotionDecoder` — LSTM decoder reconstructing motion sequences
  - `MotionAutoencoder` — full VAE with `encode()`, `decode()`, `sample()` convenience methods
  - `vae_loss()` — MSE reconstruction + KL divergence

- **`pet_soul/motion/motion_features.py`**
  - `compute_motion_stats()` — handcrafted features: avg/max speed, movement entropy, tail wag frequency (FFT), head motion range, gait regularity (autocorrelation)
  - `build_personality_vector()` — converts stats dict to numpy array

- **`pet_soul/motion/__init__.py`** — re-exports key classes

- **Added dependency:** `mediapipe>=0.10.0`

---

## Step 5 — v2.2: Behavior Engine

**Goal:** Build a probabilistic finite state machine for real-time pet behavior simulation.

### New files

- **`pet_soul/behavior/state_machine.py`**
  - `PetState` enum: IDLE, CURIOUS, PLAYFUL, ALERT, RESTING
  - `SensoryInput` dataclass: user_distance, user_moving, sound_level, time_since_interaction
  - `PetFSM` — probabilistic FSM with:
    - Weighted transition rules per state
    - Condition callbacks based on sensory input
    - 40% inertia bias to avoid twitchy state changes
    - Methods: `update()`, `force_state()`, `to_dict()`

- **`pet_soul/behavior/personality.py`**
  - `PersonalityProfile` dataclass with 7 traits: energy_level, playfulness, reactivity, tail_expressiveness, gait_regularity, vocal_energy, vocal_frequency
  - Computed composites: `sociability`, `calmness`
  - `profile_from_motion_stats()` — derives personality from motion analysis via min-max normalization

- **`pet_soul/behavior/__init__.py`** — re-exports key classes

---

## Step 6 — v2.2: Audio Module

**Goal:** Classify pet vocalizations by type and emotional state.

### New files

- **`pet_soul/audio/feature_extractor.py`**
  - `load_audio()` — loads audio via librosa (with scipy fallback)
  - `extract_mfcc()` — Mel-frequency cepstral coefficients
  - `extract_audio_stats()` — RMS energy, zero-crossing rate, spectral centroid, duration, peak amplitude

- **`pet_soul/audio/audio_classifier.py`**
  - `AudioCNN` — 1D convolutional neural network: Conv1d(n_mfcc→32) → Conv1d(32→64) → AdaptiveAvgPool → FC layers
  - `PetAudioClassifier` — wraps two CNN models:
    - Vocal type: silence, bark, meow, whine, growl, purr
    - Emotion: calm, excited, anxious, playful
  - Methods: `classify()`, `classify_file()`

- **`pet_soul/audio/__init__.py`** — re-exports key classes

- **Added dependency:** `librosa>=0.10.0`

---

## Step 7 — Runtime Export Module

**Goal:** Package pet digital twin data for Unity client consumption.

### New files

- **`pet_soul/runtime_export/unity_exporter.py`**
  - `export_to_unity()` — creates a bundle directory containing:
    - `model.glb` — 3D mesh
    - `personality.json` — personality profile
    - `motion_latent.npy` — motion autoencoder latent vector
    - `motion_stats.json` — computed motion statistics
    - `audio_stats.json` — audio analysis results
    - `animation_curves.json` — Unity-compatible animation data
    - `manifest.json` — bundle metadata
  - `export_to_zip()` — compresses bundle into a single `.zip` file
  - `keypoints_to_animation_curves()` — converts `(T, J, 3)` keypoint sequences to Unity AnimationCurve format

- **`pet_soul/runtime_export/__init__.py`** — re-exports key functions

---

## Step 8 — v3.0: World Model

**Goal:** Build a latent dynamics model for predictive pet behavior simulation.

### New files

- **`pet_soul/world_model/latent_dynamics.py`**
  - `LatentStateEncoder` — combines motion latent, personality vector, and FSM state into a unified latent representation `z`
  - `LatentDynamicsModel` — MLP predicting `z_{t+1}` from `[z_t, action]`
  - Methods: `predict()` (single step), `rollout()` (multi-step "dream" simulation)

- **`pet_soul/world_model/policy_network.py`**
  - `RewardPredictor` — MLP scoring latent states (how "good" is this state?)
  - `PolicyNetwork` — action selection via imagination:
    1. For each candidate action, predicts next state via dynamics model
    2. Scores each predicted state with reward predictor
    3. Selects action via softmax with temperature
  - `ACTION_NAMES = ["stay", "approach", "retreat", "play", "rest"]`

- **`pet_soul/world_model/__init__.py`** — re-exports key classes

---

## Step 9 — API Wiring and Final Integration

**Goal:** Expose all new modules via REST endpoints and update project configuration.

### New files

- **`pet_soul/api/routes_motion.py`**
  - `POST /motion/analyze-video` — upload video → MediaPipe pose extraction → 3D lifting → smoothing → motion stats → personality profile → stores in Supabase → returns results
  - `POST /motion/analyze-audio` — upload audio → MFCC extraction → CNN classification → returns vocal type + emotion
  - `GET /motion/personality/{pet_id}` — fetches latest personality profile from Supabase

- **`pet_soul/api/routes_export.py`**
  - `POST /export/{pet_id}/unity` — fetches pet data + personality + motion from Supabase → builds Unity bundle → returns as ZIP download

### Updated files

- **`pet_soul/api/app.py`** — imported and registered `motion_router` and `export_router`
- **`pet_soul/__init__.py`** — version bumped to `"3.0.0"`
- **`requirements.txt`** — added `mediapipe`, `librosa`, `PyJWT[crypto]`, `cryptography`, `pydantic[email]`, `supabase`; removed `SQLAlchemy`, `passlib[bcrypt]`, `bcrypt`
- **`.env.example`** — added Auth0 and Supabase environment variables
- **`CLAUDE.md`** — fully rewritten for v3.0 architecture

---

## Final Project Structure

```
PetSoul/
├── pet_soul/                          # Python package
│   ├── __init__.py                    # version = "3.0.0"
│   ├── main.py                        # Entry point (uvicorn)
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                # Config dataclass, PROJECT_ROOT
│   ├── appearance/
│   │   ├── __init__.py
│   │   ├── pipeline.py                # Orchestrator
│   │   ├── pet_detector.py            # YOLOv8
│   │   ├── attribute_extractor.py     # CLIP
│   │   ├── prompt_builder.py          # Text prompt generation
│   │   ├── meshy_generator.py         # Meshy.ai client
│   │   └── pet_profile.py             # PetProfile dataclass
│   ├── db/
│   │   ├── __init__.py
│   │   ├── auth.py                    # Auth0 JWT verification
│   │   └── supabase_client.py         # Supabase client
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                     # FastAPI app + middleware
│   │   ├── routes_auth.py             # /auth/* endpoints
│   │   ├── routes_pets.py             # /pets/* endpoints
│   │   ├── routes_motion.py           # /motion/* endpoints
│   │   └── routes_export.py           # /export/* endpoints
│   ├── motion/
│   │   ├── __init__.py
│   │   ├── pose_extractor.py          # MediaPipe keypoints
│   │   ├── lift_2d_to_3d.py           # MLP depth prediction
│   │   ├── motion_autoencoder.py      # LSTM VAE
│   │   └── motion_features.py         # Handcrafted stats
│   ├── behavior/
│   │   ├── __init__.py
│   │   ├── state_machine.py           # Probabilistic FSM
│   │   └── personality.py             # PersonalityProfile
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── feature_extractor.py       # MFCC extraction
│   │   └── audio_classifier.py        # 1D CNN classifier
│   ├── world_model/
│   │   ├── __init__.py
│   │   ├── latent_dynamics.py         # z_{t+1} = f(z_t, a_t)
│   │   └── policy_network.py          # Reward + action selection
│   └── runtime_export/
│       ├── __init__.py
│       └── unity_exporter.py          # Bundle packaging
├── tests/
│   └── test_quick.py
├── requirements.txt
├── .env.example
├── CLAUDE.md
└── CHANGELOG_v2_v3.md                 # This file
```

---

## Dependencies Changed

### Removed
- `SQLAlchemy` — replaced by Supabase
- `passlib[bcrypt]` — replaced by Auth0
- `bcrypt` — replaced by Auth0

### Added
- `PyJWT[crypto]>=2.8.0` — Auth0 RS256 token verification
- `cryptography>=41.0.0` — JWT cryptographic operations
- `pydantic[email]>=2.0.0` — request/response validation
- `supabase>=2.0.0` — Supabase Python client
- `mediapipe>=0.10.0` — pose extraction from video
- `librosa>=0.10.0` — audio feature extraction (MFCC)

### Unchanged
- `fastapi`, `uvicorn`, `pillow`, `opencv-python`, `numpy`, `scipy`, `ultralytics`, `torch`, `torchvision`, `transformers`, `accelerate`, `safetensors`, `requests`, `aiofiles`, `python-dotenv`, `python-multipart`

---

## How to Run

```bash
# Activate virtual environment
source .venv/bin/activate

# Install updated dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Auth0, Supabase, and Meshy.ai credentials

# Run the server
python -m pet_soul.main
# Server starts at http://localhost:8000
```
