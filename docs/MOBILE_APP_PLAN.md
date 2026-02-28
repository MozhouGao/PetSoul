# Pet Soul - iOS Mobile App Plan

## Overview

Build a native iOS app using Unity that lets users photograph their pet (or pick from album), send it to the existing Pet Soul backend, and view the generated 3D model interactively.

---

## Architecture

```
┌──────────────────────────────────────────┐
│           iOS Device (Unity App)          │
│                                          │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  │
│  │ Camera / │→ │ Upload   │→ │ 3D     │  │
│  │ Album    │  │ + Wait   │  │ Viewer │  │
│  │ Picker   │  │ Screen   │  │ (GLB)  │  │
│  └─────────┘  └──────────┘  └────────┘  │
│                     │              ↑      │
│                     ↓              │      │
│              ┌─────────────┐       │      │
│              │ Model       │       │      │
│              │ Gallery     │───────┘      │
│              └─────────────┘              │
└───────────────────┬──────────────────────┘
                    │ HTTPS
                    ↓
┌──────────────────────────────────────────┐
│        Pet Soul Backend (FastAPI)         │
│                                          │
│  POST /generate-3d-model                 │
│    → Detect pet (YOLOv8)                 │
│    → Extract attributes (CLIP)           │
│    → Generate 3D (Meshy.ai)              │
│    → Return JSON { profile, model_url }  │
│                                          │
│  GET /models/<filename>.glb              │
│    → Serve static GLB file               │
│                                          │
│  GET /health                             │
│    → Server status check                 │
└──────────────────────────────────────────┘
```

---

## App Screens

### 1. Home Screen
- App logo and title
- "Take Photo" button → opens device camera
- "Choose from Album" button → opens photo picker
- "My Models" button → opens gallery of previously generated models
- Server status indicator (green/red dot)

### 2. Processing Screen
- Shows uploaded pet photo as thumbnail
- Progress indicator with status messages:
  - "Uploading photo..."
  - "Detecting pet..."
  - "Generating 3D model... (1-3 minutes)"
- Cancel button
- On completion: shows pet profile summary (breed, colors, markings)
- "View 3D Model" button

### 3. 3D Model Viewer Screen
- Full-screen interactive 3D viewer
- Touch controls:
  - Single finger drag → rotate model
  - Pinch → zoom in/out
  - Two finger drag → pan
- Pet profile overlay (breed, colors, markings — collapsible)
- "Save to Gallery" button
- "Share" button (export GLB or screenshot)
- Background options (solid color, gradient, environment)

### 4. Model Gallery Screen
- Grid view of previously generated models (thumbnails)
- Tap to open in 3D viewer
- Long-press to delete
- Shows breed name and date under each thumbnail
- Pull-to-refresh

---

## Technical Stack

### Unity Project
- **Unity Version:** Unity 6 LTS (6000.x) or Unity 2022.3 LTS
- **Render Pipeline:** Universal Render Pipeline (URP) — best for mobile performance
- **Build Target:** iOS (native, NOT WebGL — better performance and native camera access)
- **Min iOS Version:** iOS 15+

### Key Unity Packages

| Package | Purpose | Install |
|---------|---------|---------|
| **glTFast** (`com.unity.cloud.gltfast`) | Runtime GLB loading with PBR materials | Unity Package Manager |
| **NativeCamera** (Yasirkula) | Native iOS camera access | OpenUPM or GitHub |
| **NativeGallery** (Yasirkula) | Native iOS photo picker | OpenUPM or GitHub |
| **TextMeshPro** | UI text rendering | Built-in |
| **Newtonsoft JSON** (`com.unity.nuget.newtonsoft-json`) | JSON parsing for API responses | Unity Package Manager |

### Backend (Existing — No Changes Needed)
- FastAPI server with `/generate-3d-model` endpoint
- Returns JSON with `profile`, `texture_prompt`, `model_url`
- Serves GLB files from `/models/` static directory

---

## Implementation Plan

### Phase 1: Unity Project Setup
1. Create new Unity project with URP template
2. Install required packages (glTFast, NativeCamera, NativeGallery, Newtonsoft JSON)
3. Configure iOS build settings (bundle ID, signing, minimum iOS version)
4. Set up scene hierarchy and basic UI canvas

### Phase 2: Camera & Photo Picker
1. Implement `PhotoCapture.cs` — handles camera and album access
2. Request iOS permissions (camera, photo library)
3. Resize/compress captured image before upload (max 1920px, JPEG quality 85%)
4. Display captured image preview on Processing Screen

### Phase 3: Backend API Integration
1. Implement `PetSoulAPI.cs` — HTTP client using `UnityWebRequest`
2. `POST /generate-3d-model` — upload image as multipart form data
3. Parse JSON response (profile, texture_prompt, model_url)
4. `GET /models/<filename>.glb` — download GLB binary
5. `GET /health` — server status check on app launch
6. Handle errors: timeout (5 min), network failure, server errors
7. Configurable backend URL (for development vs production)

### Phase 4: 3D Model Viewer
1. Implement `ModelViewer.cs` — loads and displays GLB models
2. Use glTFast `GltfImport` to load GLB from downloaded bytes or URL
3. Set up orbit camera controller:
   - Single touch drag → rotate around model
   - Pinch gesture → zoom
   - Two-finger drag → pan
4. Auto-center and auto-scale model to fit screen
5. Lighting setup: directional light + ambient for PBR materials
6. Optional: skybox or solid color background toggle

### Phase 5: Model Gallery & Persistence
1. Implement `ModelStorage.cs` — save/load models locally
2. Store models in iOS `Application.persistentDataPath`
3. Save metadata JSON alongside each GLB (profile, date, thumbnail)
4. Generate thumbnails by rendering model to RenderTexture
5. Implement gallery UI with scroll view grid
6. Delete functionality with confirmation dialog

### Phase 6: UI Polish
1. Design consistent UI theme (colors, fonts, spacing)
2. Add loading animations and progress indicators
3. Pet profile display card (breed, colors, markings, physical traits)
4. Texture prompt display (collapsible)
5. Error screens with retry buttons
6. App icon and splash screen

### Phase 7: iOS Build & Testing
1. Configure Xcode project settings
2. Test on physical iOS device (camera requires real device)
3. Test with various pet photos (dogs, different breeds, lighting conditions)
4. Performance profiling (memory, load times)
5. Handle app backgrounding during long generation

---

## Key Scripts

### `PetSoulAPI.cs`
```
Responsibilities:
- Upload pet photo to backend
- Poll/wait for generation result
- Download GLB model
- Parse pet profile from JSON response
- Health check on startup
- Configurable server URL
```

### `PhotoCapture.cs`
```
Responsibilities:
- Open native camera (NativeCamera plugin)
- Open photo album picker (NativeGallery plugin)
- Resize image for upload (max 1920px)
- Compress to JPEG (quality 85%)
- Return image as byte array for upload
```

### `ModelViewer.cs`
```
Responsibilities:
- Load GLB via glTFast at runtime
- Orbit camera with touch controls (rotate, zoom, pan)
- Auto-frame model on load
- Lighting and background setup
- Screenshot capture for sharing/thumbnails
```

### `ModelStorage.cs`
```
Responsibilities:
- Save GLB + metadata to device storage
- Load saved models list
- Generate and cache thumbnails
- Delete models
- Storage size management
```

### `UIManager.cs`
```
Responsibilities:
- Screen navigation (Home → Processing → Viewer → Gallery)
- Display pet profile information
- Progress/loading states
- Error handling and retry flows
```

---

## Data Flow

### Generate New Model
```
1. User taps "Take Photo" or "Choose from Album"
2. PhotoCapture.cs captures/picks image
3. Image resized to max 1920px, compressed to JPEG
4. UIManager shows Processing Screen
5. PetSoulAPI.cs uploads image to POST /generate-3d-model
6. Backend processes (1-3 minutes)
7. API returns JSON: { profile, texture_prompt, model_url }
8. PetSoulAPI.cs downloads GLB from model_url
9. ModelStorage.cs saves GLB + metadata locally
10. ModelViewer.cs loads and displays the 3D model
11. UIManager shows profile info overlay
```

### View Saved Model
```
1. User taps "My Models" on Home Screen
2. ModelStorage.cs loads saved model list
3. Gallery displays thumbnails in grid
4. User taps a model
5. ModelViewer.cs loads GLB from local storage
6. UIManager shows profile info overlay
```

---

## Backend Requirements

The existing backend already supports everything needed. No changes required:

| Endpoint | Used For | Status |
|----------|----------|--------|
| `POST /generate-3d-model` | Upload photo, get profile + model URL | Ready |
| `GET /models/<file>.glb` | Download generated GLB | Ready |
| `GET /health` | Check server status on app launch | Ready |

### Production Considerations
- Backend must be accessible from the iOS device (not just localhost)
- Options: deploy to cloud (AWS, GCP, Azure), use ngrok for testing, or LAN IP
- Add HTTPS for App Transport Security (iOS requires HTTPS by default)
- Consider rate limiting and authentication for production

---

## File Structure (Unity Project)

```
PetSoulApp/
├── Assets/
│   ├── Scenes/
│   │   └── MainScene.unity
│   ├── Scripts/
│   │   ├── API/
│   │   │   └── PetSoulAPI.cs
│   │   ├── Camera/
│   │   │   └── PhotoCapture.cs
│   │   ├── Viewer/
│   │   │   ├── ModelViewer.cs
│   │   │   └── OrbitCamera.cs
│   │   ├── Storage/
│   │   │   └── ModelStorage.cs
│   │   ├── UI/
│   │   │   ├── UIManager.cs
│   │   │   ├── HomeScreen.cs
│   │   │   ├── ProcessingScreen.cs
│   │   │   ├── ViewerScreen.cs
│   │   │   └── GalleryScreen.cs
│   │   └── Models/
│   │       └── PetProfile.cs
│   ├── Prefabs/
│   │   ├── UI/
│   │   │   ├── HomePanel.prefab
│   │   │   ├── ProcessingPanel.prefab
│   │   │   ├── ViewerPanel.prefab
│   │   │   └── GalleryPanel.prefab
│   │   └── ModelContainer.prefab
│   ├── Materials/
│   │   ├── SkyboxMaterial.mat
│   │   └── DefaultLit.mat
│   ├── Resources/
│   │   └── AppConfig.json
│   └── Plugins/
│       └── iOS/
│           └── (NativeCamera/NativeGallery native code)
├── Packages/
│   └── manifest.json (glTFast, Newtonsoft JSON)
└── ProjectSettings/
    └── ProjectSettings.asset
```

---

## Testing Checklist

- [ ] Camera capture works on physical iOS device
- [ ] Photo album picker works and returns image
- [ ] Image uploads successfully to backend
- [ ] Backend returns valid JSON with profile and model_url
- [ ] GLB downloads and loads in glTFast
- [ ] 3D model renders with PBR textures (not flat/single color)
- [ ] Touch controls work (rotate, zoom, pan)
- [ ] Model saves to local storage
- [ ] Gallery displays saved models
- [ ] Gallery thumbnails render correctly
- [ ] Delete model works
- [ ] App handles network errors gracefully
- [ ] App handles backend timeout (5 min) gracefully
- [ ] App resumes correctly after backgrounding during generation
- [ ] Memory usage stays under 500MB during model viewing

---

## Timeline Estimate

| Phase | Description | Complexity |
|-------|-------------|------------|
| Phase 1 | Unity project setup | Low |
| Phase 2 | Camera & photo picker | Low-Medium |
| Phase 3 | Backend API integration | Medium |
| Phase 4 | 3D model viewer | Medium-High |
| Phase 5 | Model gallery & persistence | Medium |
| Phase 6 | UI polish | Medium |
| Phase 7 | iOS build & testing | Medium |

---

## Dependencies & Requirements

### Development
- Mac with Xcode 15+ (required for iOS builds)
- Unity 6 LTS or Unity 2022.3 LTS
- Apple Developer Account ($99/year for App Store, free for personal device testing)
- Physical iOS device for camera testing (simulator has no camera)

### Runtime
- iOS 15+ device
- Network access to Pet Soul backend server
- Backend server running and accessible (LAN or cloud)

---

## Open Questions

1. **Backend hosting:** Where will the backend run for mobile access? (local network, cloud, ngrok?)
2. **Authentication:** Should the app require login, or is it open access?
3. **Offline support:** Should previously viewed models work without network?
4. **Model size:** The latest GLB was 63MB — should we compress or limit polycount for mobile?
5. **Android:** Is Android support needed in the future? (Unity supports both from same project)
