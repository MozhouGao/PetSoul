# Additional Notes & Gaps

Items not fully covered in other documentation files.

---

## Missing from .gitignore

The `avatars/` directory is intended to be excluded from version control but is **not listed** in `.gitignore`. Consider adding:

```
avatars/
```

---

## Windows Support

### install.bat
A Windows batch installer (`install.bat`) exists at the project root. It automates environment setup on Windows machines.

### WSL
The project has been developed/tested under **WSL2** (Windows Subsystem for Linux) running Linux 6.6.x on a Windows host.

---

## Model Weight Files

### YOLOv8 Nano (`yolov8n.pt`)
- Must exist in the project root before running
- ~6.5MB, committed to the repository
- If missing, Ultralytics will attempt to auto-download it

### CLIP (`openai/clip-vit-base-patch32`)
- ~300MB, **not** included in the repository
- Auto-downloaded by HuggingFace Transformers on first run
- Cached at `~/.cache/huggingface/` for subsequent runs
- First startup will be slow due to this download

### LoRA (`loras/pet_cartoon_lora.safetensors`)
- ~37.8MB, committed to the repository
- Used for cartoon-style avatar generation (not yet wired into the main pipeline)

---

## Meshy.ai Cost & Credits

| Plan | Monthly Cost | Credits/Month | Cost per Model | Models/Month |
|------|-------------|---------------|----------------|--------------|
| Pro  | ~$20        | ~1,000        | ~$0.40 (20 credits) | ~50      |

- Each image-to-3D generation uses approximately 20 credits
- Credits reset monthly
- Monitor usage at [meshy.ai dashboard](https://app.meshy.ai/)

---

## Refactoring History (TripoSR → Meshy.ai)

Documented in `REFACTOR_LOG.md` at the project root. Key points:

- **Why**: TripoSR required ~1.5GB GPU memory and memory-intensive marching cubes
- **What changed**: Replaced local 3D generation with Meshy.ai cloud API
- **Removed dependencies**: trimesh, networkx, pygltflib
- **Added**: meshy_generator.py, breed_data.py, procedural_generator.py (CPU fallback)
- **Result**: No local GPU required; better model quality

---

## Testing Prerequisites

`quick_test.py` requires the **server to be running first**:

```bash
# Terminal 1: Start server
python app.py

# Terminal 2: Run tests
python quick_test.py
```

The test script connects to `http://localhost:8000` and will fail if the server is not up.

---

## Optional Dependencies

Listed in `requirements.txt` but commented out:

| Package    | Purpose                                      | When to Enable              |
|------------|----------------------------------------------|-----------------------------|
| `pymeshlab`| Advanced mesh processing and optimization    | Post-processing 3D models   |
| `rembg`    | Background removal from pet photos           | Improving 3D generation quality |

To enable, uncomment in `requirements.txt` and run `pip install -r requirements.txt`.
