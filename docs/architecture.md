# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────┐
│           FastAPI Web Server (app.py)                │
│  Endpoints: / | /health | /test | /analyze-pet      │
│             /generate-3d-model | /generate-avatar    │
├─────────────────────────────────────────────────────┤
│       Pet3DModelPipeline (pipeline.py)               │
│                  Orchestrator                        │
├──────────┬───────────────┬──────────┬───────────────┤
│          ↓               ↓          ↓               │
│   PetDetector     AttributeExtractor  PromptBuilder │
│   (YOLOv8)        (CLIP)              (text)        │
│          ↓               ↓               ↓          │
│   Bounding Box    PetProfile         Texture Prompt │
│   + Crop                                            │
│                          ↓                          │
│                   MeshyGenerator                    │
│                   (Cloud API)                       │
│                          ↓                          │
│                   3D Model (GLB)                    │
│                          ↓                          │
│                   File Save + Response              │
└─────────────────────────────────────────────────────┘
```

## Component Responsibilities

### app.py — API Layer
- Receives HTTP requests, validates input
- Delegates processing to the pipeline
- Returns 3D model files or JSON analysis results
- Serves static test UI
- CORS enabled for all origins

### pipeline.py — Orchestrator
- Initializes all components on startup
- Coordinates the detection → extraction → generation flow
- Error handling and result packaging

### pet_detector.py — Detection
- Loads YOLOv8 nano model
- Identifies pets in images (dogs and cats)
- Returns bounding box coordinates
- Crops pet region with configurable padding

### attribute_extractor.py — Classification
- Uses CLIP for zero-shot image classification
- Extracts: breed, coat colors, markings, body type, ear shape, tail type, snout length, size class, fur length
- Falls back to pixel-based color heuristics if CLIP fails

### prompt_builder.py — Prompt Construction
- Converts PetProfile attributes into natural language prompts
- Used as texture hints for Meshy.ai 3D generation

### meshy_generator.py — 3D Generation
- Converts pet crop to base64
- Creates Meshy.ai task via REST API
- Polls task status until completion (5s intervals, 300s timeout)
- Downloads generated GLB file

### pet_profile.py — Data Model
- Dataclass holding all extracted pet attributes
- Serialization/deserialization support (to_dict/from_dict)

### config.py — Configuration
- Centralized settings (paths, thresholds, model names, API params)
- Frozen dataclass for immutability

## Data Flow

1. User uploads a pet photo (JPEG/PNG)
2. Image is validated and converted to RGB
3. YOLOv8 detects the pet and returns a bounding box
4. The pet region is cropped with padding
5. CLIP extracts breed, colors, markings, and physical attributes
6. A PetProfile dataclass is created with all attributes
7. A texture prompt is built from the profile
8. The cropped image + prompt are sent to Meshy.ai
9. Meshy.ai generates a 3D model (1–3 minutes)
10. The GLB file is downloaded and saved locally
11. The file is returned to the user with profile metadata in headers
