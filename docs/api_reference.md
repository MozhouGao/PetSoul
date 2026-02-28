# API Reference

Base URL: `http://localhost:8000`

---

## GET /

Server status and capabilities.

**Response:**
```json
{
  "status": "Pet 3D Model Generator API is running",
  "pipeline_ready": true,
  "supported_formats": ["glb", "obj", "ply", "stl"]
}
```

---

## GET /health

System health check with component readiness.

**Response:**
```json
{
  "status": "healthy",
  "detector_ready": true,
  "generator_ready": true
}
```

---

## GET /test

Redirects to the interactive web test UI at `/static/test.html`.

---

## POST /analyze-pet

Detect a pet and extract its attributes without generating a 3D model.

**Request:** `multipart/form-data`
| Field | Type   | Required | Description       |
|-------|--------|----------|-------------------|
| file  | File   | Yes      | Pet image (JPEG/PNG) |

**Response:**
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
  }
}
```

---

## POST /generate-3d-model

Full pipeline: detect pet, extract attributes, generate 3D model.

**Request:** `multipart/form-data`
| Field  | Type   | Required | Default | Description                    |
|--------|--------|----------|---------|--------------------------------|
| file   | File   | Yes      | —       | Pet image (JPEG/PNG)           |
| format | String | No       | glb     | Output format: glb, obj, ply, stl |

**Response:** Binary file download
- Content-Type: `model/gltf-binary` (for GLB)
- Custom headers:
  - `X-Pet-Profile` — JSON string of extracted pet attributes
  - `X-Model-Format` — Output format used
  - `X-Success` — `true` or `false`

**Errors:**
| Code | Description                        |
|------|------------------------------------|
| 400  | No file uploaded / invalid format  |
| 500  | Pipeline processing error          |

---

## POST /generate-avatar

Legacy endpoint (backward compatibility). Behaves identically to `/generate-3d-model`.

---

## Example Usage

```bash
# Health check
curl http://localhost:8000/health

# Analyze a pet photo
curl -X POST http://localhost:8000/analyze-pet \
  -F "file=@my_dog.jpg"

# Generate a 3D model
curl -X POST http://localhost:8000/generate-3d-model \
  -F "file=@my_dog.jpg" \
  -F "format=glb" \
  -o my_dog.glb
```
