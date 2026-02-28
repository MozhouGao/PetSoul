# Pet Soul — Full System Architecture

Complete technical architecture covering the Python backend, Unity iOS app, and Meshy.ai cloud service.

---

## System Overview

Pet Soul is a two-tier system: a **Unity iOS client** that captures pet photos, and a **Python FastAPI backend** that processes images and generates 3D models via the Meshy.ai cloud API.

```
┌─────────────────────────────────────────────────────────────────┐
│                        iOS Device                               │
│                                                                 │
│  ┌───────────────────── Unity App ───────────────────────────┐  │
│  │                                                           │  │
│  │  PhotoCapture.cs ──→ PetSoulAPI.cs ──→ ModelViewer.cs     │  │
│  │  (Camera/Album)      (HTTP Client)     (glTFast + Orbit)  │  │
│  │                           │                    ↑           │  │
│  │                           │              ModelStorage.cs   │  │
│  │                           │              (Local files)     │  │
│  │                           │                                │  │
│  │  UIManager.cs ── HomeScreen / ProcessingScreen /           │  │
│  │                  ViewerScreen / GalleryScreen               │  │
│  └───────────────────────────┬───────────────────────────────┘  │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                          HTTPS / HTTP
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                         Server (PC)                             │
│                              │                                  │
│  ┌─────────────── Python FastAPI Backend ────────────────────┐  │
│  │                           │                               │  │
│  │  app.py ← receives POST /generate-3d-model                │  │
│  │    │                                                      │  │
│  │    ↓                                                      │  │
│  │  pipeline.py (Orchestrator)                               │  │
│  │    │                                                      │  │
│  │    ├──→ pet_detector.py ──→ YOLOv8 (yolov8n.pt)          │  │
│  │    │    Detect pet, crop bounding box                     │  │
│  │    │                                                      │  │
│  │    ├──→ attribute_extractor.py ──→ CLIP (ViT-base-32)     │  │
│  │    │    Extract breed, colors, markings, physical traits  │  │
│  │    │                                                      │  │
│  │    ├──→ pet_profile.py                                    │  │
│  │    │    Create PetProfile dataclass                       │  │
│  │    │                                                      │  │
│  │    ├──→ prompt_builder.py                                 │  │
│  │    │    Build texture prompt from profile                 │  │
│  │    │                                                      │  │
│  │    └──→ meshy_generator.py ──→ Meshy.ai Cloud API ─────┐ │  │
│  │         Send image + prompt, poll, download GLB         │ │  │
│  │                                                         │ │  │
│  │  config.py (all settings)                               │ │  │
│  │                                                         │ │  │
│  │  app.py ← returns JSON { profile, prompt, model_url }   │ │  │
│  │  app.py ← serves GET /models/<file>.glb (static file)   │ │  │
│  └─────────────────────────────────────────────────────────┘ │  │
└──────────────────────────────────────────────────────────────┘  │
                                                                  │
                               ┌──────────────────────────────────┘
                               │
                          HTTPS REST API
                               │
                    ┌──────────┼──────────┐
                    │    Meshy.ai Cloud    │
                    │                     │
                    │  POST /image-to-3d  │
                    │   → Create task     │
                    │                     │
                    │  GET /image-to-3d/  │
                    │   → Poll status     │
                    │                     │
                    │  GET model_url      │
                    │   → Download GLB    │
                    └─────────────────────┘
```

---

## Layer 1: Unity iOS App (Client)

The Unity app runs on the user's iPhone. It handles photo capture, communicates with the backend, and displays 3D models.

### Components

| Script | Layer | Responsibility |
|--------|-------|----------------|
| `PhotoCapture.cs` | Input | Opens native iOS camera or photo album picker. Resizes image to max 1920px, compresses to JPEG (quality 85%). Returns byte array. |
| `PetSoulAPI.cs` | Network | HTTP client using `UnityWebRequest`. Uploads image via multipart POST, parses JSON response, downloads GLB binary. Handles timeouts and errors. |
| `ModelViewer.cs` | Rendering | Loads GLB at runtime using glTFast (`GltfImport`). Auto-centers and scales model. Captures thumbnails via `RenderTexture`. |
| `OrbitCamera.cs` | Rendering | Touch-based camera controller. Single finger = rotate, pinch = zoom, two-finger drag = pan. Mouse fallback for Unity Editor. Includes rotation inertia. |
| `ModelStorage.cs` | Persistence | Saves GLB files + metadata JSON to `Application.persistentDataPath`. Manages thumbnails, gallery index, and deletion. |
| `UIManager.cs` | UI | Screen state machine: Home → Processing → Viewer → Gallery. Controls panel visibility. |
| `HomeScreen.cs` | UI | Three buttons (camera, album, gallery). Checks server health on appear. Shows connection status dot. |
| `ProcessingScreen.cs` | UI | Shows upload progress, status messages, pet profile summary, texture prompt. Triggers GLB download after generation. |
| `ViewerScreen.cs` | UI | Overlays pet profile on 3D viewer. Toggle info visibility, reset camera view. |
| `GalleryScreen.cs` | UI | Scrollable grid of saved models. Loads thumbnails, shows breed + date labels. Tap to view, storage info footer. |
| `PetProfile.cs` | Data | C# data classes matching backend JSON: `PetProfile`, `GenerateResponse`, `HealthResponse`, `SavedModel`. |
| `AppConfig.cs` | Config | Loads `AppConfig.json` from Resources. Provides server URL, timeout, image settings. |

### Screen Flow

```
┌──────────┐    camera/album    ┌──────────────┐    done    ┌────────────┐
│          │ ────────────────→  │              │ ────────→  │            │
│   Home   │                    │  Processing  │            │   Viewer   │
│  Screen  │ ←────────────────  │    Screen    │ ←────────  │   Screen   │
│          │      cancel/back   │              │    back    │            │
└────┬─────┘                    └──────────────┘            └────────────┘
     │                                                            ↑
     │  "My Models"    ┌──────────────┐        tap model          │
     └──────────────→  │   Gallery    │ ──────────────────────────┘
                       │    Screen    │
        ←────────────  │              │
            back       └──────────────┘
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| glTFast (`com.unity.cloud.gltfast`) | 6.6.0 | Runtime GLB loading with PBR material support |
| Newtonsoft JSON (`com.unity.nuget.newtonsoft-json`) | 3.2.1 | JSON serialization |
| Universal Render Pipeline | 14.0.11 | Mobile-optimized rendering |
| TextMeshPro | 3.0.9 | UI text |
| NativeCamera (Yasirkula) | Latest | iOS native camera access |
| NativeGallery (Yasirkula) | Latest | iOS native photo album picker |

---

## Layer 2: Python FastAPI Backend (Server)

The backend runs on a PC or cloud server. It receives pet photos, processes them through an AI pipeline, and returns 3D model results.

### Components

| File | Layer | Responsibility |
|------|-------|----------------|
| `app.py` | API | FastAPI server. Receives image uploads, delegates to pipeline, serves generated GLB files as static assets. 3 endpoints. |
| `pipeline.py` | Orchestration | Coordinates the full flow: detect → extract → prompt → generate. Initializes all components on startup. |
| `pet_detector.py` | AI / Vision | Loads YOLOv8 Nano model. Detects dogs (class 15) and cats (class 16). Returns bounding box, crops pet with 20px padding. |
| `attribute_extractor.py` | AI / Vision | Loads CLIP ViT-base-32. Zero-shot classification for breed (25 labels), coat colors (15 labels), markings (9 types), and 6 physical attributes. Falls back to pixel-based color heuristic if CLIP fails. |
| `pet_profile.py` | Data | `PetProfile` dataclass holding all extracted attributes. `to_dict()` / `from_dict()` for JSON serialization. |
| `prompt_builder.py` | Text | Converts PetProfile into a natural-language texture prompt. Explicitly requests facial features (eyes, nose, mouth) and fur texture variation for Meshy.ai. |
| `meshy_generator.py` | API Client | Meshy.ai REST client. Encodes pet crop as base64, creates image-to-3D task, polls status every 5s (300s timeout), downloads resulting GLB. Sends pet crop as texture reference image. PBR enabled. |
| `config.py` | Config | Frozen dataclass with all settings: model paths, thresholds, Meshy API params, server host/port. |

### API Endpoints

| Method | Path | Request | Response | Purpose |
|--------|------|---------|----------|---------|
| `GET` | `/health` | — | `{ status, pipeline_ready, detector_ready, generator_ready }` | Server health check |
| `POST` | `/generate-3d-model` | `multipart/form-data` with `file` (JPEG/PNG) | `{ success, profile, texture_prompt, model_url, filename }` | Full pipeline: detect → analyze → generate |
| `GET` | `/models/<filename>.glb` | — | Binary GLB file | Serves generated 3D model for download |
| `GET` | `/` | — | `{ message, status, pipeline_ready }` | Root status |
| `GET` | `/test` | — | Redirect to `/static/test.html` | Web test UI (development only) |

### Pipeline Data Flow

```
Input: JPEG/PNG image (multipart upload)
         │
         ↓
    ┌─────────────────────────────────────────┐
    │ pet_detector.py                         │
    │                                         │
    │  Image ──→ YOLOv8 Nano                  │
    │            ├─ Detect COCO class 15/16   │
    │            ├─ Confidence > 0.25         │
    │            └─ Return bounding box       │
    │                                         │
    │  Image + BBox ──→ Crop (20px padding)   │
    └─────────────┬───────────────────────────┘
                  │ pet_crop (numpy RGB array)
                  ↓
    ┌─────────────────────────────────────────┐
    │ attribute_extractor.py                  │
    │                                         │
    │  pet_crop ──→ CLIP ViT-base-32          │
    │                                         │
    │  extract_breed()                        │
    │    25 breed labels → "Siberian Husky"   │
    │    + confidence score (0.89)            │
    │                                         │
    │  extract_coat_colors()                  │
    │    15 color labels → ["black", "white"] │
    │    top-3, threshold > 0.05             │
    │                                         │
    │  extract_markings()                     │
    │    9 marking types → ["facial mask"]    │
    │    threshold > 0.15                     │
    │                                         │
    │  extract_physical_attributes()          │
    │    body_type    → "athletic"            │
    │    ear_shape    → "erect"              │
    │    tail_type    → "long_curved"        │
    │    snout_length → "medium"             │
    │    size_class   → "large"              │
    │    fur_length   → "medium"             │
    └─────────────┬───────────────────────────┘
                  │ PetProfile dataclass
                  ↓
    ┌─────────────────────────────────────────┐
    │ prompt_builder.py                       │
    │                                         │
    │  PetProfile ──→ texture prompt string   │
    │                                         │
    │  "a siberian husky, with black and      │
    │   white colored fur, with facial mask   │
    │   pattern, medium-length fur texture,   │
    │   erect ears, medium snout, detailed    │
    │   face with realistic eyes with pupils  │
    │   and iris, visible nose and mouth,     │
    │   natural fur texture with color        │
    │   variation and shading, high detail,   │
    │   photorealistic textures, studio       │
    │   lighting"                             │
    └─────────────┬───────────────────────────┘
                  │ texture_prompt (string)
                  │ pet_crop (numpy array)
                  ↓
    ┌─────────────────────────────────────────┐
    │ meshy_generator.py                      │
    │                                         │
    │  1. Encode pet_crop → base64 PNG        │
    │     (used as image_url AND              │
    │      texture_image_url)                 │
    │                                         │
    │  2. POST api.meshy.ai/v1/image-to-3d   │
    │     {                                   │
    │       image_url: "data:image/png;...",  │
    │       texture_image_url: "data:...",    │
    │       texture_prompt: "a siberian...",  │
    │       ai_model: "meshy-6",             │
    │       target_polycount: 15000,          │
    │       topology: "triangle",             │
    │       enable_pbr: true,                 │
    │       should_texture: true              │
    │     }                                   │
    │     → returns task_id                   │
    │                                         │
    │  3. Poll GET /image-to-3d/{task_id}     │
    │     every 5 seconds, timeout 300s       │
    │     → wait for status "SUCCEEDED"       │
    │                                         │
    │  4. Download GLB from model_urls.glb    │
    │     → raw bytes                         │
    └─────────────┬───────────────────────────┘
                  │ GLB bytes + task metadata
                  ↓
    ┌─────────────────────────────────────────┐
    │ pipeline.py                             │
    │                                         │
    │  Save GLB to models/pet_<id>.glb        │
    │  Return {                               │
    │    profile: { breed, colors, ... },     │
    │    texture_prompt: "a siberian...",      │
    │    model_url: "/models/pet_xxx.glb",    │
    │    filename: "pet_xxx.glb"              │
    │  }                                      │
    └─────────────────────────────────────────┘
                  │
                  ↓
Output: JSON response to Unity app
```

---

## Layer 3: Meshy.ai Cloud API (External Service)

Meshy.ai handles the computationally intensive image-to-3D conversion. The backend acts as a client.

### API Flow

```
Backend                              Meshy.ai
───────                              ────────
POST /openapi/v1/image-to-3d  ────→  Create generation task
  { image_url, texture_prompt,        → Returns task_id
    enable_pbr: true,
    target_polycount: 15000 }

GET /openapi/v1/image-to-3d/{id} ──→  Check task status
  (every 5 seconds)                   → Returns { status, progress }
  ...repeat until SUCCEEDED...        → 1-3 minutes

GET {model_urls.glb}  ──────────────→  Download signed URL
                                      → Returns GLB binary (15-30MB)
```

### Meshy Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `ai_model` | meshy-6 | Latest generation model |
| `target_polycount` | 15,000 | Optimized for mobile (was 30K) |
| `topology` | triangle | Standard mesh topology |
| `enable_pbr` | true | Metallic, roughness, normal maps for realistic materials |
| `should_texture` | true | Generate texture from image + prompt |
| `texture_prompt` | (from prompt_builder) | Guides texture painting with facial detail instructions |
| `texture_image_url` | (pet crop) | Reference image for color/pattern accuracy |
| `poll_interval` | 5 seconds | How often to check task status |
| `timeout` | 300 seconds | Max wait before giving up |

### Cost

| Item | Value |
|------|-------|
| Plan | Pro (~$20/month) |
| Credits per generation | ~20 |
| Cost per model | ~$0.40 |
| Models per month | ~50 |

---

## End-to-End Request Flow

Full lifecycle of a single model generation request:

```
Time    Component              Action
─────   ─────────              ──────
0s      iOS App                User taps "Take Photo"
0.1s    PhotoCapture.cs        iOS camera opens
~3s     PhotoCapture.cs        Photo captured, resized to 1920px, JPEG 85%
3.1s    PetSoulAPI.cs          POST /generate-3d-model (uploads ~500KB JPEG)
3.5s    app.py                 Receives image, converts to numpy RGB
3.6s    pipeline.py            Starts processing
3.7s    pet_detector.py        YOLOv8 detects pet → bounding box + crop
4.5s    attribute_extractor.py CLIP extracts breed, colors, markings, physical
6s      prompt_builder.py      Builds texture prompt string
6.1s    meshy_generator.py     Encodes image as base64, POSTs to Meshy.ai
6.5s    Meshy.ai               Task created, starts generating
~60-    Meshy.ai               Generating 3D model (1-3 minutes)
180s    meshy_generator.py     Polling every 5 seconds...
~120s   Meshy.ai               Task SUCCEEDED
~122s   meshy_generator.py     Downloads GLB (~15-30MB)
~125s   pipeline.py            Saves GLB to models/ directory
~125s   app.py                 Returns JSON { profile, prompt, model_url }
~125s   PetSoulAPI.cs          Receives JSON, displays profile on ProcessingScreen
~126s   PetSoulAPI.cs          GET /models/pet_xxx.glb (downloads GLB)
~135s   ModelStorage.cs        Saves GLB + metadata to device
~135s   ModelViewer.cs         Loads GLB via glTFast, auto-frames model
~136s   ViewerScreen.cs        Displays 3D model with profile overlay
        OrbitCamera.cs         User rotates, zooms, pans the model
```

---

## Network Architecture

```
┌─────────────┐       Wi-Fi / LAN        ┌──────────────┐       HTTPS        ┌───────────┐
│             │  ──────────────────────→  │              │  ────────────────→  │           │
│  iPhone     │  POST image (500KB)      │  PC / Server │  POST base64 img   │ Meshy.ai  │
│  (Unity)    │                          │  (Python)    │                     │  Cloud    │
│             │  ←──────────────────────  │              │  ←────────────────  │           │
│             │  JSON (1KB) + GLB (15MB) │              │  GLB (15MB)        │           │
└─────────────┘                          └──────────────┘                    └───────────┘

Ports:
  iPhone → PC:       HTTP port 8000 (or HTTPS with reverse proxy)
  PC → Meshy.ai:     HTTPS port 443 (api.meshy.ai)
```

### Network Requirements

| Connection | Protocol | Data Size | Latency |
|-----------|----------|-----------|---------|
| iPhone → Backend (upload) | HTTP/HTTPS | ~500KB JPEG | < 1s (LAN) |
| iPhone → Backend (JSON response) | HTTP/HTTPS | ~1KB JSON | < 1s |
| iPhone → Backend (GLB download) | HTTP/HTTPS | 15-30MB GLB | 2-10s (LAN) |
| Backend → Meshy.ai (upload) | HTTPS | ~1MB base64 | 1-2s |
| Backend → Meshy.ai (poll) | HTTPS | ~1KB JSON | < 1s |
| Backend → Meshy.ai (download) | HTTPS | 15-30MB GLB | 5-15s |

---

## Data Model

### PetProfile (shared between backend and Unity app)

```
PetProfile
├── species: string           "dog" or "cat"
├── breed: string             "Siberian Husky"
├── breed_confidence: float   0.89
├── coat_colors: string[]     ["black", "white"]
├── markings: string[]        ["facial mask"]
├── fur_length: string        "short" | "medium" | "long" | "wire-haired"
├── body_type: string         "compact" | "athletic" | "stocky" | "slender" | "large"
├── ear_shape: string         "floppy" | "erect" | "semi-erect" | "rose" | "button"
├── tail_type: string         "long_curved" | "long_straight" | "curled" | "short" | "docked"
├── snout_length: string      "flat" | "short" | "medium" | "long"
├── size_class: string        "toy" | "small" | "medium" | "large" | "giant"
└── leg_length: string        "short" | "medium" | "long"
```

### JSON Response (POST /generate-3d-model)

```json
{
  "success": true,
  "profile": {
    "species": "dog",
    "breed": "Siberian Husky",
    "breed_confidence": 0.89,
    "coat_colors": ["black", "white"],
    "markings": ["facial mask"],
    "fur_length": "medium",
    "body_type": "athletic",
    "ear_shape": "erect",
    "tail_type": "long_curved",
    "snout_length": "medium",
    "size_class": "large",
    "leg_length": "medium"
  },
  "texture_prompt": "a siberian husky, with black and white colored fur...",
  "model_url": "/models/pet_a1b2c3d4_1771566605.glb",
  "filename": "pet_a1b2c3d4_1771566605.glb"
}
```

### Local Storage (iOS Device)

```
Application.persistentDataPath/
├── models/
│   ├── pet_a1b2c3d4.glb          (15-30MB GLB file)
│   ├── pet_e5f6g7h8.glb
│   └── ...
├── thumbnails/
│   ├── a1b2c3d4.jpg              (256x256 screenshot)
│   ├── e5f6g7h8.jpg
│   └── ...
└── models_index.json             (metadata for all saved models)
```

---

## File Map — All Components

### Python Backend (`/pet_soul/`)

```
pet_soul/
├── app.py                    API server (FastAPI)
├── pipeline.py               Orchestrator
├── config.py                 Settings (frozen dataclass)
├── pet_detector.py           YOLOv8 detection
├── attribute_extractor.py    CLIP classification
├── prompt_builder.py         Texture prompt generation
├── meshy_generator.py        Meshy.ai API client
├── pet_profile.py            PetProfile dataclass
├── quick_test.py             CLI test script
├── requirements.txt          Python dependencies
├── .env                      MESHY_API_KEY
├── yolov8n.pt                YOLOv8 Nano weights (6.5MB)
├── static/test.html          Web test UI (dev only)
└── models/                   Generated GLB output
```

### Unity iOS App (`/pet_soul/PetSoulApp/`)

```
PetSoulApp/
├── Assets/
│   ├── Scripts/
│   │   ├── API/
│   │   │   └── PetSoulAPI.cs         HTTP client
│   │   ├── Camera/
│   │   │   └── PhotoCapture.cs       Camera + album
│   │   ├── Viewer/
│   │   │   ├── ModelViewer.cs        GLB loader (glTFast)
│   │   │   └── OrbitCamera.cs        Touch controls
│   │   ├── Storage/
│   │   │   └── ModelStorage.cs       Local persistence
│   │   ├── UI/
│   │   │   ├── UIManager.cs          Screen navigation
│   │   │   ├── HomeScreen.cs         Main menu
│   │   │   ├── ProcessingScreen.cs   Generation progress
│   │   │   ├── ViewerScreen.cs       3D viewer overlay
│   │   │   └── GalleryScreen.cs      Saved models grid
│   │   └── Models/
│   │       ├── PetProfile.cs         Data classes
│   │       └── AppConfig.cs          Config loader
│   └── Resources/
│       └── AppConfig.json            Server URL + settings
├── Packages/
│   └── manifest.json                 Unity package dependencies
└── SETUP_GUIDE.md                    Unity Editor setup instructions
```

---

## AI Models Used

| Model | Size | Runs On | Purpose |
|-------|------|---------|---------|
| YOLOv8 Nano | 6.5MB | Backend (CPU/GPU) | Pet detection in photos |
| CLIP ViT-base-32 | ~300MB | Backend (CPU/GPU) | Breed, color, marking, physical attribute classification |
| Meshy-6 | Cloud | Meshy.ai servers | Image-to-3D mesh generation with PBR textures |

### Model Loading

- **YOLOv8**: Loaded from `yolov8n.pt` on backend startup
- **CLIP**: Auto-downloaded from HuggingFace on first run (~300MB), cached at `~/.cache/huggingface/`
- **Meshy-6**: No local model — cloud API call via REST

---

## Security Considerations

| Concern | Current State | Production Recommendation |
|---------|--------------|--------------------------|
| API transport | HTTP (plaintext) | Use HTTPS with TLS certificate |
| Authentication | None | Add API key or JWT auth to backend |
| Meshy API key | `.env` file on server | Use secrets manager (AWS Secrets, etc.) |
| iOS App Transport | Requires HTTPS by default | Enable HTTPS or add ATS exception for dev |
| Image data | Sent as JPEG over network | HTTPS encrypts in transit |
| Local storage | Unencrypted on device | Acceptable for non-sensitive 3D models |
| CORS | Allow all origins (`*`) | Restrict to known origins in production |
