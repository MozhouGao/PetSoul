# Project Structure

```
pet_soul/
├── docs/                          # Documentation (this folder)
│   ├── tech_stack.md              # Technologies and dependencies
│   ├── architecture.md            # System design and data flow
│   ├── api_reference.md           # API endpoints and usage
│   ├── skills_required.md         # Technical skills needed
│   ├── project_structure.md       # This file
│   └── development_guide.md       # Setup, testing, and contribution guide
│
├── app.py                         # FastAPI server and API endpoints
├── pipeline.py                    # Main orchestration pipeline
├── config.py                      # Centralized configuration
├── pet_profile.py                 # PetProfile dataclass (data model)
├── pet_detector.py                # YOLOv8 pet detection
├── attribute_extractor.py         # CLIP-based attribute extraction
├── prompt_builder.py              # Texture prompt construction
├── meshy_generator.py             # Meshy.ai 3D generation client
├── breed_data.py                  # Breed body proportion parameters
├── procedural_generator.py        # CPU fallback mesh generator
├── model3d_generator.py           # TripoSR integration (deprecated)
├── quick_test.py                  # CLI test script
│
├── static/
│   └── test.html                  # Browser-based test UI
│
├── models/                        # Generated 3D model output
│   └── pet_*.glb / .stl           # Output files (UUID + timestamp)
│
├── avatars/                       # Avatar output (future use)
├── loras/
│   └── pet_cartoon_lora.safetensors  # LoRA weights (future use)
│
├── TripoSR/                       # Git submodule (deprecated)
│   ├── tsr/                       # TripoSR model code
│   ├── run.py                     # Inference script
│   └── ...
│
├── yolov8n.pt                     # YOLOv8 nano model weights
├── requirements.txt               # Python dependencies
├── .python-version                # Python 3.10.14
├── .gitignore                     # Git ignore rules
├── .env                           # Environment variables (not committed)
├── README.md                      # Project overview
├── REFACTOR_LOG.md                # TripoSR → Meshy.ai transition log
└── LORA_SETUP.md                  # LoRA configuration guide
```

## Key Directories

| Directory | Purpose | Git-tracked |
|-----------|---------|-------------|
| `docs/`   | Project documentation | Yes |
| `static/` | Web UI assets | Yes |
| `models/` | Generated 3D output files | Partially |
| `avatars/` | Avatar output (future) | No (.gitignore) |
| `loras/`  | LoRA model weights | Yes |
| `TripoSR/` | Deprecated submodule | Yes (submodule) |
