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
- [ ] **Onion Skinning in Preview Player**: Toggleable ghost frames to inspect motion arcs and spacing.
- [ ] **8-Directional Movement Generator**: Automatic generation of 8-way directional sprites (N, NE, E, SE, S, SW, W, NW) for Top-Down and Isometric.
- [ ] **Normal Map & Depth Map Generation**: Real-time normal map baking for dynamic 2D lighting in Godot and Unity.
- [ ] **Interactive Chroma-Key Color Picker**: Custom eyedropper tool for transparent background selection in the web UI.

---

## Version 0.3.0 (Planned - Tileset & Autotile Studio)

- [ ] **Wang & Autotiling Engine**: Support for 3x3 minimal autotiles (cliffs, paths, water shorelines).
- [ ] **Seamless Tiling Inspector**: Automatic edge-matching validation for background textures.
- [ ] **Game Engine Exporters**: Native export presets for Godot TileMap resources, Tiled (.tmx), and Unity RuleTiles.

---

## Version 0.4.0 (Future - High-Fidelity Character Consistency)

- [ ] **ControlNet & IP-Adapter Pipelines**: Image reference conditioning for 100% character identity preservation across actions.
- [ ] **Multi-Action Master Sheets**: Generate complete action suites (Walk, Run, Jump, Attack, Die) in a single unified sheet.
- [ ] **Batch Item Catalog Generator**: Generate entire collections of themed items (e.g. 20 distinct swords) in one click.
