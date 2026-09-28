# Roadmap - GameAssetGenerator

Development and feature roadmap for the GameAssetGenerator project.

---

## Version 0.1.0 (Current - Core Architecture & Foundations)

- [x] **Modular Project Architecture**: Separation into `lib/`, `modules/`, `prompts/`, `settings/`, `web/`, `workflows/`, `documentation/`, `output/`.
- [x] **Three Core Perspectives**: Side-View (Platformer), Top-Down (RPG/RTS), Isometric (2.5D Dimetric).
- [x] **Customizable Sizing**: Presets (16x16 to 512x512) and arbitrary pixel dimensions with Nearest-Neighbor / Lanczos filters.
- [x] **Animation Phase Engine**: Walk, Sit Down, Jump, Run, Attack, and Idle with custom step counts (2–16 frames).
- [x] **ComfyUI API Client**: REST & WebSocket connectivity, dynamic node injection (dimensions, prompts, seeds).
- [x] **LM Studio Integration**: Local LLM prompt enhancement and keyframe planning with offline fallback.
- [x] **Extensible Module System**: `BaseAssetModule` lifecycle hooks (`on_prompt_prepare`, `on_workflow_prepare`, `on_postprocess`, `register_routes`).
- [x] **Starter Modules**:
  - `character_animator` (Silhouette & pose consistency)
  - `item_generator` (Inventory & icon framing)
  - `palette_quantizer` (Pico-8 & Game Boy retro shaders)
- [x] **Categorized Project Output**: Hierarchical folder storage (`output/<Project>/<Category>/<Asset>/`) with frames, spritesheets, GIF, WebP, and engine JSON.
- [x] **Modern Web Studio**: Interactive animation player, spritesheet viewer, frame strip, project gallery, and instant mock preview mode.
- [x] **Git Repository Setup**: Comprehensive `.gitignore` for Python, IDEs, and output tracking.

---

## Version 0.2.0 (Character-Centric Grouping & Portrait Perspective)

- [x] **Character-Centric Master Entity Grouping**: Automatic `master_reference.png` generation, `character.json` manifest, and anchor inheritance for walking, sitting, jumping, attacking, and talking.
- [x] **Portrait / Bust Perspective**: Dedicated 4th perspective for jRPGs, visual novels, dialogue avatars, and status screens.
- [x] **Dialogue & Lip-Sync Animation Action (`talk`)**: Configurable 2- to 6-step talking cycles with mouth open/close and eye blinking.
- [x] **96x96 jRPG Portrait Preset**: Standard resolution preset for classic retro RPG face graphics.
- [x] **Dynamic ComfyUI Model Engine**: Real-time Checkpoint discovery, LoRA injection with weight controls, UNet, VAE, Sampler/Scheduler selection, and auto-fallback.
- [x] **Integrated LM Studio Model Manager**: Live loaded model detection and in-app model loading.
- [x] **Sequential Frame-by-Frame Generation Engine**: Img2Img frame chaining (`denoise: 0.38`), eliminating composite strip slicing distortion.
- [x] **Onion Skinning in Preview Player**: Toggleable ghost frames (previous/next frame semi-transparent) to inspect motion arcs, timing, and spacing.
- [x] **Interactive Chroma-Key Color Picker**: Custom eyedropper tool for transparent background selection and live tolerance tuning in the web UI.
- [x] **Normal Map & Depth Map Generation**: Real-time normal map baking (Sobel gradient filter) for dynamic 2D lighting in Godot and Unity.
- [x] **8-Directional Movement Generator**: Automatic generation of 8-way directional sprites (N, NE, E, SE, S, SW, W, NW) for Top-Down and Isometric with auto-mirror symmetry.

---

## Version 0.3.0 (Game Genre Presets & Point & Click Adventure Studio)

- [x] **Game Genre Quick Presets**:
  - **Point & Click Adventure**: 3/4 standing full-body (1:2 aspect ratio), walking, interact, look, and multi-layer cloth changes.
  - **Classic 2D Platformer**: Side-view running, jumping arcs, melee attacks, and crouch.
  - **jRPG / Visual Novel**: Bust dialogue portraits, emotion lip-sync, and reaction cutouts.
  - **Top-Down ARPG / Tactics**: 4-way / 8-way orthogonal movement and grid-aligned idle.
- [ ] **Cloth Change / Strip Animation Action (`cloth_change`)**:
  - Multi-phase outfit layer transitions with tuned img2img denoise (preserving 100% anatomy and face while modifying clothing layers).
- [ ] **Wang & Autotiling Engine**: Support for 3x3 minimal autotiles (cliffs, paths, water shorelines).
- [ ] **Seamless Tiling Inspector**: Automatic edge-matching validation for background textures.
- [ ] **Game Engine Exporters**: Native export presets for Godot TileMap resources, Tiled (.tmx), UnrealEngine and Unity RuleTiles.

---

## Version 0.4.0 (Released - Video Motion Engine & High-Fidelity Character Consistency)

- [x] **MiniMax H3 Reference-to-Video Motion Engine**: Direct spatiotemporal 3D attention conditioning locking character identity, lighting, and wardrobe 100% frozen across all animation frames.
- [x] **Automatic BiRefNet AI Cutout Pipeline**: Neural background removal integrated for multi-frame video extraction.
- [x] **Non-Directional Perspective Guards**: Hardened isolation preventing accidental 8-directional suite creation for full-body/portrait assets.
- [ ] **Multi-Action Master Sheets**: Generate complete action suites (Walk, Run, Jump, Attack, Die) in a single unified sheet.
- [ ] **Batch Item Catalog Generator**: Generate entire collections of themed items (e.g. 20 distinct swords) in one click.

## Version 0.9.0 (Future - 3D Asset Generation)

- [ ] **3D Asset Generation**: Generate 3D assets for/like characters, items, and environments.
- [ ] **3D Asset Export**: Export 3D assets in various formats (e.g. GLB, FBX, OBJ).
- [ ] **3D Asset Preview**: Preview 3D assets in the web UI.
