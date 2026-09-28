# Changelog - GameAssetGenerator

All notable changes and milestones of the GameAssetGenerator project are documented here.

---

## [0.3.0] - 2026-09-28

### Added
- **8-Directional Movement Generator (Top-Down & Isometric)**:
  - Added full 8-way directional generation (`S`, `SW`, `W`, `NW`, `N`, `NE`, `E`, `SE`), 4-cardinal (`S`, `W`, `N`, `E`), and 4-isometric (`SE`, `SW`, `NW`, `NE`) movement suites.
  - Symmetrical Auto-Mirroring: Automatically mirrors right-facing angles (`E`, `SE`, `NE`) from left-facing angles (`W`, `SW`, `NW`), cutting GPU generation time by 40% while guaranteeing exact pixel symmetry.
  - Multi-Row Directional Spritesheet: Packs all directional animations into structured 2D spritesheets (`spritesheet.png`) with Godot SpriteFrames and Unity Sprite Editor metadata.
  - Interactive 360° Compass Rose Widget: Added visual compass rose rosette in the Studio UI with mode selector pills and direction display.
  - Directional Preview Switcher: Allows switching between angles in the animation preview player.
- **Onion Skinning in Preview Player**:
  - Toggleable ghost frames (`🧅`) rendering semi-transparent previous and next animation frames directly on the canvas to inspect motion arcs, timing, and spacing.
- **Interactive Chroma-Key Color Picker**:
  - Color picker input and Eyedropper tool with live tolerance slider (5–80) in the Studio toolbar.
  - New endpoint `/api/tools/chroma_key` for boundary-constrained transparency removal without erasing internal character whites.
- **2D Normal Map & Depth Map Generation**:
  - Vectorized 3x3 Sobel filter in `SpriteProcessor` baking tangent-space normal maps (`normal_map.png`) and depth maps (`depth_map.png`) directly from spritesheets for dynamic 2D lighting in Godot 4 and Unity URP.
  - New endpoint `/api/tools/bake_maps` for on-demand map baking.
  - Spritesheet Map Switcher (Diffuse / Normal Map / Depth Map) and live 2D normal preview shader in player.
  - Dedicated export buttons for Normal Maps and Depth Maps.
- **Sequential Frame-by-Frame Generation Engine**:
  - Replaced single-strip slicing with true sequential frame-by-frame generation.
  - Implemented dynamic frame chaining via ComfyUI `/upload/image`, `LoadImage`, and `VAEEncode`.
  - Frame $i$ references Frame $i-1$ via latent img2img (`denoise: 0.38`), ensuring 100% character identity, clothing, hair, and lighting consistency while cleanly articulating movement (mouth lip sync, eye blinks).
  - Automatic `master_reference.png` initialization for Frame 1.
- **Portrait & Bust Resolution Presets**:
  - Added `256x384` (Portrait Bust), `512x768` (HD Dialogue Portrait), and `512x1024` (Visual Novel Full Bust) to `settings/resolutions.json`.
  - Auto-selects `512x768` upon selecting the Portrait perspective in the Studio UI.

### Fixed
- **Elimination of Multi-Head Collage / Expression Sheet Artifacts**:
  - Removed ambiguous plural prompt tokens (`frames`, `speech portrait frames`, `cycle sequence`) in `modules/character_animator.py` and `prompts/animation_breakdowns.json` that caused diffusion models to render collage sheets.
  - Added comprehensive negative prompt guards against multiple characters, character sheets, expressions sheets, collages, duplicate heads, and border icons.
  - Added automated prompt sanitation for portraits to remove contradictory full-body keywords.

---

## [0.2.0] - 2026-09-28

### Added
- **Portrait Perspective (jRPG & Visual Novel)**:
  - Added 4th perspective `portrait` tailored for dialogue boxes, character busts, visual novels, and status menus.
  - Dedicated prompt prefixes and negative prompt filters preventing full-body, distant, or floor angles.
  - Geometry alignment and grid metadata type `dialogue_bust`.
- **Dialogue Animation Action (`talk`)**:
  - Added `talk` ("Talk (Dialogue / Lip Sync)") animation action with 2, 3, 4, and 6-frame steps for lip-sync and eye blinking.
  - Detailed animation cues and breakdowns in `prompts/animation_breakdowns.json`.
  - Added support in `modules/character_animator.py` for dialogue speech poses.
- **jRPG Portrait Resolution Preset**:
  - Added `96x96` ("jRPG Portrait") preset in `settings/resolutions.json`.
- **Stylized Mock Generator for Portraits**:
  - Built interactive mock frame renderer in `main.py` generating jRPG tunic busts, heads, hairstyles, blinking eyes, and mouth lip-sync frames.
- **Web UI 4-Card Perspective Grid**:
  - Added responsive 4-column perspective selector in `web/index.html` and `web/css/style.css` with custom SVG bust icon.
- **Console Log Quieting**:
  - Minimized Uvicorn access log spam and fixed empty 204 response handling.
- **Linux & macOS Start Script (`start.sh`)**:
  - Added bash launcher with automatic Python interpreter detection and virtual environment support (`.venv`/`venv`).
  - Added `.gitattributes` to ensure LF line endings for shell scripts.
- **Dynamic Checkpoint, LoRA, UNet & VAE Selection (ComfyUI)**:
  - Added live model discovery endpoint `/api/comfy/models` retrieving all installed Checkpoints, UNets, LoRAs, VAEs, Samplers, and Schedulers.
  - Implemented dynamic LoRA injection into ComfyUI workflow graph with customizable model and clip strength weights.
  - Implemented automatic checkpoint validation and fallback: eliminates `Value not in list: ckpt_name` errors by automatically matching installed image models instead of hardcoded strings.
  - Added folder-grouped dropdowns in the Web UI for easy navigation across models.
- **LM Studio Integration & Active Model Management**:
  - Added `/api/lm/models` and `/api/lm/load-model` endpoints for real-time model status and in-app loading.
  - Added LM Studio model selector and active loaded model indicator in the Studio interface.
  - Automatic loaded model detection and auto-load fallback for prompt enhancement and animation planning.

---

## [0.1.0] - 2026-09-28

### Initial Release & Core Foundations

#### Added

- **Core Library Architecture (`lib/`)**:
  - `lib/comfy_client.py`: Full ComfyUI REST & WebSocket interface with node parameter injection and progress polling.
  - `lib/lm_client.py`: LM Studio client for AI prompt refinement and keyframe pose planning with offline fallback.
  - `lib/perspective_manager.py`: Full support for Side-View, Top-Down, and Isometric (2.5D dimetric) projections.
  - `lib/sprite_processor.py`: Pixel scaling (Nearest Neighbor, Bilinear, Lanczos), background transparency, strip slicing, spritesheet packing, animated GIF/WebP creation, and engine export metadata.
  - `lib/project_manager.py`: Structured project hierarchy under `output/<Project>/<Category>/<Asset>/`.
  - `lib/module_interface.py` & `lib/module_manager.py`: Pluggable module system with lifecycle hooks.
  - `lib/config_manager.py`: Centralized configuration management for `settings/`.
- **Extensible Modules (`modules/`)**:
  - `modules/character_animator.py`: Silhouette and pose consistency for animated characters.
  - `modules/item_generator.py`: Specific framing for inventory icons and collectible props.
  - `modules/palette_quantizer.py`: Retro palette shader for Pico-8 and Game Boy aesthetics.
- **Character Entity Grouping & Master Reference System**:
  - Grouping of all character animations under `output/<Project>/characters/<Character_ID>/`.
  - Automatic `master_reference.png` generation to serve as the visual anchor for subsequent motions.
  - `character.json` manifest tracking all animations (walk, sit, jump, attack, idle) tied to the character.
  - Consistent seed and base appearance prompt inheritance across all movement cycles.
  - Interactive UI card showing Master Asset thumbnail and animation count.
- **Settings & Config (`settings/`)**:
  - `config.json`, `categories.json`, `perspectives.json`, `resolutions.json`, `animations.json` (all fully localized in English).
- **Prompt Presets (`prompts/`)**:
  - `system_prompts.json`, `style_presets.json`, `animation_breakdowns.json`.
- **ComfyUI Workflows (`workflows/`)**:
  - `sprite_sheet_generator.json` and `pixel_asset_single.json`.
- **Modern Web Studio (`web/`)**:
  - Dark theme with glassmorphism and cyber/game-dev aesthetics.
  - Interactive animation player with frame-stepping, play/pause, FPS slider, and 1x–8x pixel zoom.
  - Tabbed views for Animation Preview, Spritesheet, Individual Frames, and Project Gallery.
  - Mock/demo mode for instantaneous testing without GPU delay.
- **Documentation (`documentation/`)**:
  - `USER_GUIDE.md`: Comprehensive English user manual.
  - `MODULE_DEVELOPMENT.md`: Developer guide for building custom plugins.
  - `COMFYUI_SETUP.md`: ComfyUI setup and workflow configuration.
  - `LM_STUDIO_INTEGRATION.md`: Prompt design and LM Studio configuration.
- **Launchers & Git Configuration**:
  - `start.bat`: Windows batch launcher with syntax-safe jumps.
  - `start.ps1`: Native PowerShell launcher.
  - `.gitignore`: Rules for virtual environments, outputs, and build caches.
