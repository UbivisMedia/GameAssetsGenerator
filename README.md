# GameAssetGenerator

A modular AI studio designed for generating 2D and 2.5D game assets with consistent animation phases, customizable resolutions, spritesheet packing, and native game engine exports.

![Perspectives](https://img.shields.io/badge/Perspectives-SideView%20|%20TopDown%20|%20Isometric%20|%20Portrait-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Backend](https://img.shields.io/badge/Backend-ComfyUI%20%26%20LM%20Studio-purple)

---

## 🌟 Key Features

- **4 Dedicated Perspectives**:
  - **Side-View**: For jump 'n' run, platformers, metroidvanias, and 2D action games.
  - **Top-Down**: For classic 2D RPGs, RTS, strategy, and roguelikes (orthogonal angle).
  - **Isometric (2.5D)**: True 2:1 dimetric projection (30°/45° grid alignment) for tactical RPGs and city builders.
  - **Portrait (jRPG / VN)**: Bust and face avatars for dialogue boxes, visual novels, character menus, and status screens.
- **Customizable Resolutions & Sizing**:
  - Presets: `16x16`, `24x24`, `32x32`, `48x48`, `64x64`, `96x96`, `128x128`, `256x256`, `512x512`.
  - Custom width and height inputs.
  - Scaling filters: *Nearest Neighbor* (preserves crisp retro pixel edges without blurring), *Bilinear*, or *Lanczos*.
- **Automatic Animation Phases (Step Sequences)**:
  - Preset motions: **Walk Cycle**, **Sit Down**, **Jump Cycle**, **Run Cycle**, **Attack / Slash**, **Talk (Dialogue / Lip Sync)**, **Idle Stance**, or **Custom**.
  - Configurable step count (2 to 16 individual frames).
  - AI-assisted keyframe planning via LM Studio or rule-based animation breakdown templates.
- **Dynamic Model & Engine Selection (ComfyUI & LM Studio)**:
  - Live discovery and folder-grouped selection of all local Checkpoints, LoRAs (with adjustable strength), UNets, VAEs, Samplers, and Schedulers.
  - Automatic fallback prevention (prevents `ckpt_name not in list` errors by auto-detecting valid installed image checkpoints).
  - Integrated LM Studio model loader, status indicator, and prompt refinement.
- **Modular Plugin Architecture (`modules/`)**:
  - Easily extend the generator by dropping Python modules into `modules/`.
  - Simple `BaseAssetModule` lifecycle hooks (`on_prompt_prepare`, `on_workflow_prepare`, `on_postprocess`, `register_routes`).
- **Structured Project Output**:
  - Organized systematically: `output/<Project>/<Category>/<Asset_Name>/`
  - Automatically produces:
    - Transparent individual frame PNGs (`frames/frame_01.png`, ...)
    - Packed grid spritesheet (`spritesheet.png`)
    - Animated previews (`preview.gif` and `preview.webp`)
    - Engine metadata (`metadata.json` compatible with Godot 4 `SpriteFrames` and Unity Sprite Atlas)
- **Modern Web Interface**:
  - Interactive animation player with play/pause, frame-stepping, FPS speed slider (1–30 FPS).
  - Pixel zoom controls (1x to 8x) with pixelated rendering.
  - Real-time ComfyUI and LM Studio connection monitors.
  - Instant mock preview mode for rapid testing without GPU delays.

---

## 📂 Project Structure

| Directory / File | Description |
|---|---|
| [`documentation/`](file:///e:/GameAssetGenerator/documentation) | Guides for users, module developers, and ComfyUI setup |
| [`lib/`](file:///e:/GameAssetGenerator/lib) | Core Python libraries (ComfyUI client, LM client, Sprite Engine, etc.) |
| [`modules/`](file:///e:/GameAssetGenerator/modules) | Plugin directory for custom modules (`BaseAssetModule`) |
| [`output/`](file:///e:/GameAssetGenerator/output) | Categorized project deliverables (`<Project>/<Category>/<Asset>/`) |
| [`prompts/`](file:///e:/GameAssetGenerator/prompts) | LM Studio prompt templates, art styles, and keyframe breakdowns |
| [`settings/`](file:///e:/GameAssetGenerator/settings) | JSON configurations (categories, resolutions, perspectives, server) |
| [`web/`](file:///e:/GameAssetGenerator/web) | Web interface (HTML5, Modern CSS, Vanilla JS) |
| [`workflows/`](file:///e:/GameAssetGenerator/workflows) | ComfyUI API workflows for sprite generation |
| [`main.py`](file:///e:/GameAssetGenerator/main.py) | Application server & orchestration engine (FastAPI / Uvicorn) |
| [`start.bat`](file:///e:/GameAssetGenerator/start.bat) | Windows 1-click batch launcher |
| [`start.ps1`](file:///e:/GameAssetGenerator/start.ps1) | PowerShell native start script |
| [`start.sh`](file:///e:/GameAssetGenerator/start.sh) | Linux / macOS bash start script |
| [`.gitignore`](file:///e:/GameAssetGenerator/.gitignore) | Git ignore rules for virtual environments, outputs, and caches |

---

## 🚀 Quickstart

1. **Launch the server**:
   - **Windows**: Double-click [`start.bat`](file:///e:/GameAssetGenerator/start.bat) or run `.\start.ps1` in PowerShell
   - **Linux / macOS**: Run `./start.sh` in terminal (`chmod +x start.sh`)
   - *(or `python3 main.py` / `py -3.10 main.py`)*

2. **Open your browser**:
   Navigate to **[http://127.0.0.1:7865](http://127.0.0.1:7865)**.

3. **Generate your first asset**:
   - Select your perspective (e.g. *Isometric*).
   - Select resolution (e.g. *64x64*) and motion (e.g. *Walk* with 4 steps).
   - Enter your prompt and click **Generate Asset** (with ComfyUI) or **Mock Preview** (instant test).
   - Play with the animation preview, adjust FPS/zoom, and export the spritesheet or engine JSON.

---

## 📖 Documentation

- [User Guide (USER_GUIDE.md)](file:///e:/GameAssetGenerator/documentation/USER_GUIDE.md)
- [Module Development Guide (MODULE_DEVELOPMENT.md)](file:///e:/GameAssetGenerator/documentation/MODULE_DEVELOPMENT.md)
- [ComfyUI Integration (COMFYUI_SETUP.md)](file:///e:/GameAssetGenerator/documentation/COMFYUI_SETUP.md)
- [LM Studio Integration (LM_STUDIO_INTEGRATION.md)](file:///e:/GameAssetGenerator/documentation/LM_STUDIO_INTEGRATION.md)
