# Changelog - GameAssetGenerator

All notable changes and milestones of the GameAssetGenerator project are documented here.

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
