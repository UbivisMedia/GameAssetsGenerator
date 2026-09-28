# ComfyUI Integration & Workflow Setup

**GameAssetGenerator** communicates directly with a local ComfyUI instance via its official REST and WebSocket APIs.

---

## 1. Prerequisites & Connectivity

- **Default URL**: `http://127.0.0.1:8188` (configurable in `settings/config.json`).
- Launch ComfyUI on your machine as usual:
  ```powershell
  python main.py --listen 127.0.0.1 --port 8188
  ```
- The status pill in the web application header will immediately reflect the connection state:
  - 🟢 **ComfyUI: Online** (Ready for inference)
  - 🔴 **ComfyUI: Offline (Mock Available)** (Fallback mode active for instant previews)

---

## 2. ComfyUI Workflows (`workflows/`)

Workflows are standard ComfyUI API JSON graphs located in `workflows/`:

1. `workflows/sprite_sheet_generator.json`:
   - Primary workflow for multi-frame animation strips.
   - Generates a horizontal strip with evenly spaced frames.
   - `lib/sprite_processor.py` slices the strip into individual frames and scales them to your exact target resolution.

2. `workflows/pixel_asset_single.json`:
   - Single-asset generation for props, inventory items, or static tiles.

### Dynamic Node Injection
`lib/comfy_client.py` inspects the workflow and automatically sets:
- **`CLIPTextEncode`**: Injects positive and negative prompts (including perspective cues).
- **`EmptyLatentImage`**: Updates latent width, height, and batch size.
- **`KSampler`**: Sets seed, inference steps, and CFG scale.
- **`SaveImage`**: Intercepts the generated image filename for automatic retrieval.

---

## 3. Background Removal & Transparency

The generator provides two transparent cutout methods:
1. **Built-in SpriteProcessor** (`SpriteProcessor.make_transparent`):
   - Fast, local algorithm that identifies neutral/white studio backgrounds and converts them to 8-bit alpha with feathered edge preservation.
2. **ComfyUI Rembg Node**:
   - Workflows can incorporate neural background removal nodes (e.g. `comfyui-rembg`) directly in `workflows/`.
