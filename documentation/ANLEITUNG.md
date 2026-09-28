# GameAssetGenerator - Benutzeranleitung

Willkommen beim **GameAssetGenerator**, dem modularen Studio zur KI-gestützten Erzeugung von 2D- und 2.5D-Spiele-Assets mit Animationsphasen, Spritesheets und Engine-Export.

---

## 1. Übersicht & Kernfunktionen

Der Generator unterstützt:
- **Drei Perspektiven**:
  1. **Seitenansicht (Side-View)**: Für Jump'n'Runs, 2D-Platformer und Metroidvanias.
  2. **Vogelperspektive (Top-Down)**: Für klassische 2D-Rollenspiele, Strategiespiele und Rogue-likes.
  3. **Isometrisch (Isometric 2.5D)**: Echte dimetrische 2:1-Projektion (30°/45° Winkel) für Taktik-RPGs und Aufbauspiele.
- **Individuell definierbare Größen**:
  - Retro-Presets: `16x16`, `24x24`, `32x32`, `48x48`, `64x64`, `128x128`, `256x256`, `512x512`
  - Frei anpassbare Pixel-Dimensionen (Breite × Höhe)
  - Wählbare Skalierungsfilter: *Nearest Neighbor* für scharfe Pixel-Art, *Bilinear* oder *Lanczos* für HD-Grafiken.
- **Automatische Animationsphasen (Steps)**:
  - Vordefinierte Aktionen wie **Laufen (Walk Cycle)**, **Hinsetzen (Sit Down)**, **Sprung (Jump)**, **Rennen (Run)**, **Angriff (Attack)**, **Warten (Idle)** oder **Benutzerdefiniert**.
  - Flexible Step-Anzahl (2 bis 16 Einzel-Frames).
  - KI-gestützte Aufteilung der Posen über LM Studio oder regelbasierte Animationstemplates.
- **Verbindungen & KI-Backends**:
  - **ComfyUI**: Generierung über lokale Stable Diffusion Workflows via WebSocket- & REST-API.
  - **LM Studio**: Lokales LLM zur automatischen Verfeinerung von Prompts, Perspektiven-Treue und Keyframe-Planung.
  - **Offline/Mock-Modus**: Test- und Vorschau-Generator für sofortige Inspektion ohne GPU-Wartezeit.

---

## 2. Ordnerstruktur

Das Projekt ist klar strukturiert:

```text
GameAssetGenerator/
├── documentation/   # Anleitungen für Nutzer und Entwickler
├── lib/             # Aufgeteilte Python-Bibliotheken (ComfyUI, LM Studio, Sprites, Module, etc.)
├── modules/         # Plugin-Verzeichnis für Erweiterungen (BaseAssetModule)
├── output/          # Ausgabeverzeichnis für generierte Assets
│   └── <Projekt>/
│       └── <Rubrik>/
│           └── <Asset_Name>/
│               ├── frames/          # Einzelne transparente PNG-Frames (frame_01.png, ...)
│               ├── spritesheet.png  # Zusammengefügtes Spritesheet
│               ├── preview.gif      # Animierte Vorschau (GIF)
│               ├── preview.webp     # Animierte Vorschau (WebP)
│               └── metadata.json    # Metadaten & Godot/Unity Exportdaten
├── prompts/         # LM Studio Prompts, Stilvorlagen & Keyframe-Definitionen
├── settings/        # JSON-Einstellungen (Perspektiven, Kategorien, Auflösungen, Server)
├── web/             # Webinterface (HTML5, modernes CSS, Vanilla JavaScript)
├── workflows/       # ComfyUI JSON-Workflows
├── main.py          # Backend-Server (FastAPI / Uvicorn)
└── start.bat        # Windows-Startskript
```

---

## 3. Programm starten

Führe einfach die `start.bat` aus oder starte die Anwendung über das Terminal:

```powershell
py -3.10 main.py
```

Öffne anschließend deinen Browser unter:
👉 **`http://127.0.0.1:7865`**

---

## 4. Schritt-für-Schritt-Anleitung

### 4.1 Projekt und Rubrik wählen
- Wähle ein bestehendes Projekt oder klicke auf `+`, um ein neues Spielprojekt anzulegen.
- Wähle die Rubrik (z.B. *Charaktere*, *Items*, *Props*, *Tilesets*, *Effekte* oder *UI*).
- Gib einen eindeutigen Asset-Namen ein (z.B. `held_laufen_isometrisch`).

### 4.2 Perspektive auswählen
Klicke auf eine der drei Perspektiven-Karten:
- **Seitenansicht**: Richtet das Asset flach auf der Horizontallinie aus.
- **Vogelperspektive**: Stellt das Asset direkt von oben dar.
- **Isometrisch**: Winkelt das Asset für ein 2.5D-Raster an.

### 4.3 Auflösung & Animations-Steps einstellen
- Wähle ein Pixel-Preset (z.B. `64x64`) oder gib freie Pixelmaße ein.
- Wähle die gewünschte Bewegung (z.B. *Laufen*, *Hinsetzen*, *Sprung*).
- Schiebe den Step-Regler auf die gewünschte Frame-Anzahl (z.B. 4 Steps).
- Optional: Klicke auf **"LM Studio Posen generieren"**, um die Keyframe-Posen aufzuschlüsseln.

### 4.4 Prompt & Stil
- Wähle den gewünschten Grafikstil (z.B. *16-Bit Pixel Art*, *32-Bit GBA*, *Handgezeichnet 2D*, etc.).
- Gib deine Idee ein (z.B. `Zwergenkrieger mit goldener Axt`).
- Klicke optional auf **"KI-Prompt verfeinern"**, um den Prompt via LM Studio zu optimieren.

### 4.5 Generierung & Live-Vorschau
- Klicke auf **"Asset generieren"** (mit ComfyUI) oder **"Mock / Demo Vorschau"** (sofortiger Test).
- Im rechten Bereich startet direkt der **Animations-Player**:
  - Play/Pause & Frame-Step
  - FPS-Geschwindigkeitsregler
  - Zoomstufen von 1x bis 8x mit pixelgenauem Rendering
  - Transparenz-Schachbrettmuster umschaltbar
- Wechsle zwischen den Tabs:
  - **Animation Preview**: Live animierte Vorschau
  - **Spritesheet**: Das komplette zusammengefügte Grid
  - **Einzel-Frames**: Alle Frames einzeln aufgelistet
  - **Projekt-Galerie**: Alle bisher erstellten Assets im Projekt

### 4.6 Export in Spiele-Engines
In der Box unter der Vorschau stehen Direktlinks bereit:
- **Spritesheet PNG**: Direkt einsatzbereit für Godot, Unity, GameMaker oder Unreal Engine.
- **Animiertes GIF / WebP**: Für Web-Vorschauen oder Dokumentation.
- **Godot/Unity JSON (`metadata.json`)**: Enthält Frame-Koordinaten, Frame-Dauern und Animationsdefinitionen.
