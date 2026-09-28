# GameAssetGenerator - User Manual

Welcome to **GameAssetGenerator**, the modular AI-powered studio designed to create 2D and 2.5D game assets with animation phases, packed spritesheets, and game-engine exports.

---

## 1. Overview & Capabilities

- **Three Perspectives**:
  1. **Side-View**: For jump 'n' run, platformers, metroidvanias, and side-scrolling action.
  2. **Top-Down**: For classic 2D RPGs, RTS, strategy, and roguelikes.
  3. **Isometric (2.5D)**: True 2:1 dimetric projection (30°/45° angle) for tactical RPGs and isometric games.
- **Customizable Sizes & Resolutions**:
  - Retro presets: `16x16`, `24x24`, `32x32`, `48x48`, `64x64`, `128x128`, `256x256`, `512x512`.
  - Custom pixel dimensions (Width × Height).
  - Resampling filters: *Nearest Neighbor* for pixel-art crispness, *Bilinear* or *Lanczos* for high-detail smooth art.
- **Animation Phases & Step Planning**:
  - Presets: **Walk Cycle**, **Sit Down**, **Jump Cycle**, **Run Cycle**, **Attack / Slash**, **Idle Stance**, or **Custom**.
  - Flexible step counts (2 to 16 individual frames).
  - AI-assisted keyframe planning via LM Studio or rule-based templates.
- **AI Integrations**:
  - **ComfyUI**: Local Stable Diffusion workflows via WebSocket and REST API.
  - **LM Studio**: Local LLM endpoint for prompt enrichment and keyframe breakdowns.
  - **Mock / Demo Mode**: Instant preview generation without GPU requirements.

---

## 2. Directory Layout

```text
GameAssetGenerator/
├── documentation/   # Guides and documentation
├── lib/             # Modular Python libraries
├── modules/         # Custom plugin modules (BaseAssetModule)
├── output/          # Categorized outputs: output/<Project>/<Category>/<Asset>/
│   └── <Project>/
│       └── <Category>/
│           └── <Asset_Name>/
│               ├── frames/          # Transparent PNG frames (frame_01.png, ...)
│               ├── spritesheet.png  # Packed spritesheet grid
│               ├── preview.gif      # Animated GIF preview
│               ├── preview.webp     # Animated WebP preview
│               └── metadata.json    # Godot 4 & Unity metadata export
├── prompts/         # LM Studio prompts & art styles
├── settings/        # System and configuration files (JSON)
├── web/             # Modern web dashboard (HTML, CSS, JS)
├── workflows/       # ComfyUI JSON workflows
├── main.py          # FastAPI application server
├── start.bat        # Windows batch launcher
├── start.ps1        # PowerShell launcher
├── start.sh         # Linux / macOS shell launcher
└── .gitignore       # Git ignore rules
```

---

## 3. Starting the Studio

- **Windows**: Double-click [`start.bat`](file:///./start.bat) or run `.\start.ps1` in PowerShell.
- **Linux / macOS**: Run `./start.sh` in your terminal (`chmod +x start.sh`).

Open your browser at:
👉 **`http://127.0.0.1:7865`**

---

## 4. Step-by-Step Workflow

1. **Select Project & Category**: Choose an existing project or click `+` to create a new one. Select the category (e.g. Characters, Items, Props, Tilesets, Effects, UI).
2. **Character-Centric Grouping (Characters Category)**:
   - When **Characters & Creatures** is selected, the **Character Entity** selector appears.
   - Choose an existing character or click `+` to create a new character group with an appearance prompt.
   - The **Master Reference Anchor** card shows the character's primary image, perspective, and animation count.
   - When checked, the generator automatically anchors the new animation cycle to the character's visual design and seed!
3. **Select Perspective**: Click on Side-View, Top-Down, Isometric, or Portrait (jRPG / Dialogue).
4. **Configure Resolution & Steps**: Choose a size preset (e.g. 64x64 or 96x96 for jRPG portraits), choose an animation action (e.g. Walk, Sit, Jump, Talk, Idle), and set the step slider (e.g. 4 frames).
5. **Draft Prompt & Style**: Choose your art style (e.g. 16-Bit Pixel Art) and enter your description. Optionally click "Enhance with AI".
6. **Generate & Preview**: Click "Generate Asset" (with ComfyUI) or "Mock / Demo Preview".
7. **Preview & Export**: Use the built-in player to test playback speed and zoom levels. Download the spritesheet, animated GIF, or Godot/Unity JSON. All character animations are organized neatly under `output/<Project>/characters/<Character_ID>/animations/<Action>/`.
