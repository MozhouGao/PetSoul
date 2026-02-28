# Technology Stack

## Languages
- **Python 3.10.14** — Primary language for all backend logic

## Web Framework
- **FastAPI 0.104.1** — Async REST API framework
- **Uvicorn 0.24.0** — ASGI server for running FastAPI
- **python-multipart 0.0.6** — File upload handling

## Machine Learning & AI

### Pet Detection
- **Ultralytics YOLOv8 Nano** (`yolov8n.pt`, ~6.5MB) — Real-time object detection
  - Detects COCO classes: dog (15), cat (16)
  - Confidence threshold: 0.25

### Attribute Extraction
- **OpenAI CLIP** (`openai/clip-vit-base-patch32`, ~300MB) — Zero-shot image classification
  - Breed identification (25 dog breeds)
  - Coat color extraction (15 colors)
  - Marking detection (9 types)
  - Physical attribute classification (6 categories)

### Deep Learning Frameworks
- **PyTorch 2.1.0** — Tensor computation and model inference
- **TorchVision 0.16.0** — Image transforms and pretrained models
- **Transformers 4.35.0** (HuggingFace) — CLIP model loading
- **Accelerate 0.24.1** — Hardware-agnostic model loading
- **SafeTensors 0.4.0+** — Safe model weight serialization

## 3D Generation
- **Meshy.ai API** (Cloud) — Image-to-3D model generation
  - Model: meshy-6
  - Output: GLB, OBJ, PLY, STL formats
  - Polycount: 30,000 triangles
  - Requires `MESHY_API_KEY` environment variable

### Fallback / Deprecated
- **Procedural Generator** — CPU-only mesh creation from geometric primitives
- **TripoSR** (submodule, deprecated) — Local GPU-based 3D generation

## Image Processing
- **Pillow (PIL) 10.1.0** — Image loading, conversion, cropping
- **OpenCV 4.8.1** — Advanced image processing

## Scientific Computing
- **NumPy 1.23–1.25** — Array operations
- **SciPy 1.11.4** — Scientific algorithms

## Utilities
- **Requests 2.31.0+** — HTTP client for Meshy.ai API
- **aiofiles 2.3.1** — Async file I/O
- **python-dotenv 1.0.0** — Environment variable loading from `.env`

## Future / Unused
- **LoRA** (`pet_cartoon_lora.safetensors`, ~37.8MB) — Stable Diffusion fine-tuning adapter for cartoon-style avatars (not yet integrated)
