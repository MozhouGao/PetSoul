# Development Guide

## Prerequisites

- Python 3.9–3.11 (project uses 3.10.14)
- Git
- Meshy.ai Pro account (for 3D generation)

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd pet_soul

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
echo "MESHY_API_KEY=msy_your_key_here" > .env
```

## Running the Server

```bash
python app.py
```

Server starts at `http://localhost:8000`. Visit `http://localhost:8000/test` for the web UI.

## Testing

### CLI Test Script
```bash
python quick_test.py
```

Runs three tests:
1. Health check — verifies server and component readiness
2. Analyze pet — tests detection + attribute extraction
3. Generate 3D model — full pipeline test

### Manual API Testing
```bash
# Health check
curl http://localhost:8000/health

# Analyze a pet
curl -X POST http://localhost:8000/analyze-pet -F "file=@photo.jpg"

# Generate 3D model
curl -X POST http://localhost:8000/generate-3d-model \
  -F "file=@photo.jpg" -F "format=glb" -o output.glb
```

### Web UI Testing
Open `http://localhost:8000/test` in a browser for the interactive test interface.

## Environment Variables

| Variable        | Required | Description                          |
|-----------------|----------|--------------------------------------|
| `MESHY_API_KEY` | Yes      | API key from meshy.ai Pro account    |

Store in a `.env` file at the project root (loaded by python-dotenv).

## Common Issues

### "No pet detected in image"
- Ensure the image clearly shows a dog or cat
- Try a higher resolution image
- Check that `yolov8n.pt` exists in the project root

### "Generator not ready"
- Verify `MESHY_API_KEY` is set correctly
- Check Meshy.ai account has available credits

### CLIP model slow to load
- First run downloads ~300MB of model weights
- Subsequent runs use the HuggingFace cache
- CPU inference is slower than GPU but fully functional

### Out of memory
- CLIP + YOLOv8 together use ~1–2GB RAM
- Close other memory-intensive applications
- Consider using a machine with at least 4GB RAM

## Viewing 3D Models

Generated `.glb` files can be viewed with:
- **Online:** [glTF Viewer](https://gltf-viewer.donmccurdy.com/)
- **Desktop:** Blender, MeshLab, 3D Viewer (Windows)
- **Programmatic:** trimesh (Python), three.js (JavaScript)
