"""
GameAssetGenerator - Main Application Server
FastAPI backend providing REST endpoints, static asset serving,
and orchestration between ComfyUI, LM Studio, and the Sprite Engine.
"""

from datetime import datetime
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from PIL import Image, ImageDraw

from lib.config_manager import ConfigManager
from lib.comfy_client import ComfyClient
from lib.lm_client import LMClient
from lib.perspective_manager import PerspectiveManager
from lib.sprite_processor import SpriteProcessor
from lib.project_manager import ProjectManager
from lib.module_manager import ModuleManager

from version import __version__

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("GameAssetGenerator")
logger.setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
OUTPUT_DIR = BASE_DIR / "output"
WORKFLOWS_DIR = BASE_DIR / "workflows"

# Initialize subsystems
config_mgr = ConfigManager(BASE_DIR)
cfg = config_mgr.config
comfy_client = ComfyClient(base_url=cfg.get("comfyui", {}).get("url", "http://127.0.0.1:8188"))
lm_client = LMClient(base_url=cfg.get("lm_studio", {}).get("url", "http://127.0.0.1:1234/v1"))
persp_mgr = PerspectiveManager(config_mgr.perspectives)
proj_mgr = ProjectManager(OUTPUT_DIR)
mod_mgr = ModuleManager(BASE_DIR / "modules")
mod_mgr.discover_and_load_modules()
app = FastAPI(title="GameAssetGenerator API", version="{__version__}")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register module custom routes if any
mod_mgr.register_routes(app)

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


# Static file mounts
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")


# Pydantic Schemas
class EnhancePromptRequest(BaseModel):
    user_prompt: str
    category: str
    perspective: str
    style_id: Optional[str] = "pixel_art_16bit"


class PlanAnimationRequest(BaseModel):
    asset_name: str
    action: str
    steps_count: int
    perspective: str


class GenerateAssetRequest(BaseModel):
    project_name: str
    rubrik: str
    asset_name: str
    prompt: str
    negative_prompt: Optional[str] = ""
    perspective: str
    action: str
    steps_count: int = 4
    fps: int = 8
    width: int = 64
    height: int = 64
    scaling_mode: str = "nearest"
    workflow_name: Optional[str] = "sprite_sheet_generator.json"
    seed: Optional[int] = None
    steps: int = 25
    cfg: float = 7.5
    remove_background: bool = True
    palette_mode: Optional[str] = None
    mock_demo: bool = False
    character_id: Optional[str] = None
    character_name: Optional[str] = None
    set_as_master: bool = False
    use_character_reference: bool = True
    checkpoint: Optional[str] = None
    unet: Optional[str] = None
    lora: Optional[str] = None
    lora_strength: float = 1.0
    vae: Optional[str] = None
    sampler_name: Optional[str] = None
    scheduler: Optional[str] = None
    direction: Optional[str] = "S"
    mirror_symmetry: bool = True
    chroma_color: Optional[str] = None
    chroma_tolerance: int = 35


class ChromaKeyRequest(BaseModel):
    image_url: str
    color: Optional[str] = None
    tolerance: int = 35


class BakeMapsRequest(BaseModel):
    image_url: str
    strength: float = 2.0
    invert_y: bool = False



# API Routes
@app.get("/")
def read_root():
    """Serves the main web application."""
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"status": "GameAssetGenerator API is running. web/index.html not found."})


@app.get("/api/status")
def get_service_status():
    """Checks health and availability of ComfyUI and LM Studio."""
    return {
        "comfyui": comfy_client.check_connection(),
        "lm_studio": lm_client.check_connection(),
        "loaded_modules_count": len(mod_mgr.modules)
    }


@app.post("/api/tools/chroma_key")
def tool_chroma_key(req: ChromaKeyRequest):
    """Applies interactive chroma-key background removal with custom color & tolerance."""
    rel = req.image_url.strip().lstrip("/")
    if rel.startswith("output/"):
        rel = rel[len("output/"):]
    target_path = OUTPUT_DIR / rel
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {target_path}")

    parsed_color = None
    if req.color:
        c = req.color.strip().lstrip("#")
        if len(c) == 6:
            try:
                parsed_color = (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
            except Exception:
                pass

    try:
        img = Image.open(target_path).convert("RGBA")
        cleaned = SpriteProcessor.make_transparent(img, bg_color=parsed_color, tolerance=req.tolerance)
        cleaned.save(target_path, format="PNG")

        parent = target_path.parent
        normal_path = parent / "normal_map.png"
        depth_path = parent / "depth_map.png"
        if target_path.name == "spritesheet.png":
            nm = SpriteProcessor.generate_normal_map(cleaned)
            nm.save(normal_path, format="PNG")
            dm = SpriteProcessor.generate_depth_map(cleaned)
            dm.save(depth_path, format="PNG")

        return {
            "status": "success",
            "image_url": f"{req.image_url}?t={int(datetime.now().timestamp())}",
            "tolerance": req.tolerance,
            "color": req.color
        }
    except Exception as e:
        logger.error(f"Chroma key processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tools/bake_maps")
def tool_bake_maps(req: BakeMapsRequest):
    """Bakes tangent-space 2D normal map and grayscale depth map on demand."""
    rel = req.image_url.strip().lstrip("/")
    if rel.startswith("output/"):
        rel = rel[len("output/"):]
    target_path = OUTPUT_DIR / rel
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {target_path}")

    try:
        img = Image.open(target_path).convert("RGBA")
        parent = target_path.parent
        normal_path = parent / "normal_map.png"
        depth_path = parent / "depth_map.png"

        nm = SpriteProcessor.generate_normal_map(img, strength=req.strength, invert_y=req.invert_y)
        nm.save(normal_path, format="PNG")

        dm = SpriteProcessor.generate_depth_map(img)
        dm.save(depth_path, format="PNG")

        base_url = req.image_url.rsplit("/", 1)[0]
        ts = int(datetime.now().timestamp())
        return {
            "status": "success",
            "normal_map": f"{base_url}/normal_map.png?t={ts}",
            "depth_map": f"{base_url}/depth_map.png?t={ts}"
        }
    except Exception as e:
        logger.error(f"Map baking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/perspectives/directions")
def get_perspective_directions():
    """Returns the list of 8-way spatial directions and order presets."""
    return {
        "directions": persp_mgr.list_directions(),
        "order_8_way": persp_mgr.ORDER_8_WAY,
        "order_4_cardinal": persp_mgr.ORDER_4_CARDINAL,
        "order_isometric_4": persp_mgr.ORDER_ISOMETRIC_4
    }


@app.get("/api/comfy/models")
def get_comfy_models():
    """Returns all available ComfyUI checkpoints, unets, loras, vaes, and samplers."""
    return comfy_client.get_available_models()


@app.get("/api/lm/models")
def get_lm_models():
    """Returns all installed models in LM Studio and their loading state."""
    return {
        "models": lm_client.get_models(),
        "selected_model": lm_client.model
    }


@app.post("/api/lm/load-model")
def load_lm_model(data: Dict[str, str]):
    """Dynamically loads a model into LM Studio via CLI/API."""
    model_id = data.get("model_id", "").strip()
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")
    res = lm_client.load_model(model_id)
    return res


@app.get("/api/config")
def get_system_config():
    """Returns all configuration data, categories, perspectives, resolutions, and modules."""
    config_mgr.reload_all()
    # Read style presets
    style_path = BASE_DIR / "prompts" / "style_presets.json"
    styles = []
    if style_path.exists():
        try:
            with open(style_path, "r", encoding="utf-8") as f:
                styles = json.load(f).get("styles", [])
        except Exception:
            pass

    return {
        "config": config_mgr.config,
        "categories": config_mgr.categories,
        "perspectives": config_mgr.perspectives,
        "resolutions": config_mgr.resolutions,
        "animations": config_mgr.animations,
        "styles": styles,
        "modules": mod_mgr.list_modules()
    }


@app.get("/api/projects")
def list_projects():
    """Returns available projects and their categorized rubriken."""
    projects = proj_mgr.list_projects()
    result = []
    for p in projects:
        rubriken = proj_mgr.list_rubriken(p)
        result.append({"name": p, "rubriken": rubriken})
    return {"projects": result}


@app.post("/api/projects/create")
def create_project(data: Dict[str, str]):
    project_name = data.get("project_name", "").strip()
    rubrik = data.get("rubrik", "").strip()
    if not project_name:
        raise HTTPException(status_code=400, detail="Project name is required")
    p_dir = proj_mgr.get_project_dir(project_name)
    if rubrik:
        proj_mgr.get_rubrik_dir(project_name, rubrik)
    return {"status": "success", "project": project_name, "rubrik": rubrik}


@app.get("/api/characters")
def list_characters(project: Optional[str] = None):
    """Lists all grouped characters and their animation suites in a project."""
    if not project:
        projects = proj_mgr.list_projects()
        if not projects:
            return {"characters": []}
        project = projects[0]
    chars = proj_mgr.list_characters(project)
    return {"project": project, "characters": chars}


@app.post("/api/characters/create")
def create_character_endpoint(data: Dict[str, Any]):
    """Pre-creates a character entity to group future animation phases."""
    project_name = data.get("project_name", "DefaultProject")
    name = data.get("name", "").strip()
    character_id = data.get("character_id", "").strip() or ProjectManager.sanitize_name(name)
    if not character_id:
        raise HTTPException(status_code=400, detail="Character name or ID is required")

    c_dir = proj_mgr.get_character_dir(project_name, character_id)
    char_file = c_dir / "character.json"
    char_data = {
        "character_id": character_id,
        "name": name or character_id.replace("_", " ").title(),
        "project": project_name,
        "perspective": data.get("perspective", "side_view"),
        "base_prompt": data.get("base_prompt", ""),
        "base_negative_prompt": data.get("base_negative_prompt", ""),
        "seed": data.get("seed", -1),
        "style_id": data.get("style_id", "pixel_art_16bit"),
        "created_at": datetime.now().isoformat(),
        "animations": {}
    }
    with open(char_file, "w", encoding="utf-8") as f:
        json.dump(char_data, f, indent=2, ensure_ascii=False)

    return {"status": "success", "character": char_data}


@app.get("/api/assets")
def list_assets(project: Optional[str] = None, rubrik: Optional[str] = None):

    """Lists generated assets from the output directory."""
    if not project:
        projects = proj_mgr.list_projects()
        if not projects:
            return {"assets": []}
        project = projects[0]
    assets = proj_mgr.list_assets(project, rubrik)
    return {"project": project, "assets": assets}


@app.post("/api/lm/enhance-prompt")
def enhance_prompt(req: EnhancePromptRequest):
    """Enriches prompt via LM Studio or rule-based fallback."""
    persp_data = persp_mgr.get_perspective(req.perspective)
    # Style lookup
    style_path = BASE_DIR / "prompts" / "style_presets.json"
    style_prompt = "pixel art style"
    if style_path.exists():
        try:
            with open(style_path, "r", encoding="utf-8") as f:
                styles = json.load(f).get("styles", [])
                for s in styles:
                    if s.get("id") == req.style_id:
                        style_prompt = s.get("prompt", style_prompt)
                        break
        except Exception:
            pass

    enhanced = lm_client.enhance_asset_prompt(
        user_prompt=req.user_prompt,
        category=req.category,
        perspective_data=persp_data,
        style_prompt=style_prompt
    )
    return enhanced


@app.post("/api/lm/plan-animation")
def plan_animation(req: PlanAnimationRequest):
    """Generates animation step poses and descriptions."""
    persp_data = persp_mgr.get_perspective(req.perspective)
    act_data = config_mgr.get_animation_action(req.action)
    templates = []
    if act_data and "step_descriptions" in act_data:
        templates = act_data["step_descriptions"].get(str(req.steps_count), [])

    steps = lm_client.plan_animation_steps(
        asset_name=req.asset_name,
        action=req.action,
        steps_count=req.steps_count,
        perspective_data=persp_data,
        step_templates=templates
    )
    return {"action": req.action, "steps_count": req.steps_count, "steps": steps}


def create_mock_sprite_frame(
    width: int,
    height: int,
    perspective: str,
    action: str,
    step_idx: int,
    total_steps: int,
    asset_name: str,
    direction: str = "S"
) -> Image.Image:
    """
    Creates an authentic, stylized placeholder game sprite for instant testing
    when ComfyUI is not currently generating or in mock mode.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Base silhouette color
    color_palette = [
        (66, 135, 245), (235, 87, 87), (39, 174, 96),
        (242, 153, 74), (155, 81, 224), (45, 156, 219)
    ]
    primary_color = color_palette[hash(asset_name) % len(color_palette)]

    cx, cy = width // 2, height // 2
    r = min(width, height) // 4

    # Animation offset
    phase = (step_idx / max(1, total_steps)) * 6.283
    import math
    bob_y = int(math.sin(phase) * (height * 0.08))
    stride_x = int(math.cos(phase) * (width * 0.12))

    if perspective == "isometric":
        # Draw isometric diamond base
        iso_w = width * 0.6
        iso_h = iso_w * 0.5
        top = (cx, cy + height * 0.15)
        right = (cx + iso_w / 2, cy + height * 0.15 + iso_h / 2)
        bottom = (cx, cy + height * 0.15 + iso_h)
        left = (cx - iso_w / 2, cy + height * 0.15 + iso_h / 2)
        draw.polygon([top, right, bottom, left], fill=(220, 220, 220, 180), outline=(100, 100, 100, 255))
        # Draw character elevated
        char_y = cy - int(height * 0.1) + bob_y
        draw.ellipse([cx - r, char_y - r, cx + r, char_y + r], fill=primary_color, outline=(255, 255, 255, 255))
    elif perspective == "top_down":
        # Draw top-down circular head and shoulder nubs
        draw.ellipse([cx - r - 4, cy - r + bob_y, cx + r + 4, cy + r + bob_y], fill=(40, 40, 40, 200))
        draw.ellipse([cx - r, cy - r + bob_y, cx + r, cy + r + bob_y], fill=primary_color, outline=(255, 255, 255, 255))
        # Directional pointer/eyes
        dir_vecs = {
            "N": (0, -1), "NE": (0.7, -0.7), "E": (1, 0), "SE": (0.7, 0.7),
            "S": (0, 1), "SW": (-0.7, 0.7), "W": (-1, 0), "NW": (-0.7, -0.7)
        }
        dx, dy = dir_vecs.get(direction.upper(), (0, 1))
        eye_dist = r * 0.55
        pointer_x = cx + int(dx * eye_dist)
        pointer_y = cy + int(dy * eye_dist) + bob_y
        draw.ellipse([pointer_x - 3, pointer_y - 3, pointer_x + 3, pointer_y + 3], fill=(255, 255, 255, 255))
        # Foot step indicator
        draw.ellipse([cx - r + stride_x, cy + r + bob_y, cx - r + stride_x + 6, cy + r + bob_y + 6], fill=(240, 240, 240, 255))
    elif perspective == "portrait":
        # Draw jRPG dialogue bust portrait
        bust_y = int(height * 0.65)
        # Shoulders / tunic
        draw.polygon([
            (int(width * 0.15), height),
            (int(width * 0.35), bust_y),
            (int(width * 0.65), bust_y),
            (int(width * 0.85), height)
        ], fill=primary_color, outline=(20, 20, 20, 255))
        # Neck
        neck_w = int(width * 0.15)
        draw.rectangle([cx - neck_w, bust_y - int(height * 0.1), cx + neck_w, bust_y], fill=(245, 215, 185, 255))
        # Face / Head
        face_r = int(min(width, height) * 0.28)
        head_cy = int(height * 0.4) + (bob_y // 2)
        draw.ellipse([cx - face_r, head_cy - face_r, cx + face_r, head_cy + face_r], fill=(250, 225, 200, 255), outline=(30, 30, 30, 255))
        # Hair locks
        draw.arc([cx - face_r - 2, head_cy - face_r - 4, cx + face_r + 2, head_cy], 180, 360, fill=primary_color, width=max(2, int(face_r * 0.4)))
        # Eyes
        eye_y = head_cy - int(face_r * 0.1)
        eye_spacing = int(face_r * 0.45)
        blink = (step_idx == total_steps - 1) and (action in ('talk', 'idle', 'walk'))
        if blink:
            draw.line([(cx - eye_spacing - 4, eye_y), (cx - eye_spacing + 4, eye_y)], fill=(30, 30, 30, 255), width=2)
            draw.line([(cx + eye_spacing - 4, eye_y), (cx + eye_spacing + 4, eye_y)], fill=(30, 30, 30, 255), width=2)
        else:
            draw.ellipse([cx - eye_spacing - 3, eye_y - 4, cx - eye_spacing + 3, eye_y + 4], fill=(30, 30, 30, 255))
            draw.ellipse([cx + eye_spacing - 3, eye_y - 4, cx + eye_spacing + 3, eye_y + 4], fill=(30, 30, 30, 255))
        # Mouth
        mouth_y = head_cy + int(face_r * 0.5)
        mouth_open = (step_idx % 2 == 1) if action == 'talk' else False
        if mouth_open:
            draw.ellipse([cx - 4, mouth_y - 3, cx + 4, mouth_y + 3], fill=(180, 50, 50, 255), outline=(30, 30, 30, 255))
        else:
            draw.line([(cx - 4, mouth_y), (cx + 4, mouth_y)], fill=(120, 50, 50, 255), width=2)
    else: # side_view
        # Side view with leg movement
        ground_y = int(height * 0.85)
        draw.line([(0, ground_y), (width, ground_y)], fill=(120, 120, 120, 200), width=1)
        body_y = cy + bob_y
        draw.rectangle([cx - r // 2, body_y - r, cx + r // 2, body_y + r], fill=primary_color, outline=(20, 20, 20, 255))
        # Head
        head_r = r // 2
        draw.ellipse([cx - head_r, body_y - r - head_r * 2, cx + head_r, body_y - r], fill=(245, 215, 185, 255), outline=(20, 20, 20, 255))
        # Legs
        draw.line([(cx - 4, body_y + r), (cx - 4 + stride_x, ground_y)], fill=(30, 30, 30, 255), width=2)
        draw.line([(cx + 4, body_y + r), (cx + 4 - stride_x, ground_y)], fill=(60, 60, 60, 255), width=2)

        if direction.upper() in ("W", "SW", "NW"):
            img = SpriteProcessor.mirror_frame(img)

    return img


def get_step_cue(action: str, step_idx: int, total_steps: int, perspective: str) -> str:
    """
    Returns specific visual pose/action cues for animation step idx (0-indexed).
    Combines settings/animations.json and prompts/animation_breakdowns.json.
    """
    action_data = config_mgr.get_animation_action(action)
    step_desc = ""
    if action_data:
        step_descriptions = action_data.get("step_descriptions", {})
        if str(total_steps) in step_descriptions:
            descs = step_descriptions[str(total_steps)]
            if step_idx < len(descs):
                step_desc = descs[step_idx]
        elif step_descriptions:
            first_key = list(step_descriptions.keys())[0]
            descs = step_descriptions[first_key]
            if descs:
                step_desc = descs[step_idx % len(descs)]

    bd_file = BASE_DIR / "prompts" / "animation_breakdowns.json"
    bd_cues = []
    if bd_file.exists():
        try:
            with open(bd_file, "r", encoding="utf-8") as f:
                bd_data = json.load(f).get("breakdowns", {}).get(action, {})
                cues = bd_data.get(f"{perspective}_cues", [])
                if cues:
                    bd_cues.append(cues[step_idx % len(cues)])
        except Exception:
            pass

    parts = []
    if step_desc:
        parts.append(step_desc)
    if bd_cues:
        parts.extend(bd_cues)

    return ", ".join(parts)


@app.post("/api/generate")
def generate_asset(req: GenerateAssetRequest):
    """
    Main orchestration endpoint for asset generation.
    Connects modules, prompt preparation, ComfyUI execution, frame extraction,
    transparency, scaling, packing, and project storage.
    """
    logger.info(f"Generating asset: {req.asset_name} in {req.project_name}/{req.rubrik}")

    # Check if this generation belongs to a grouped character
    char_data = None
    char_id = req.character_id
    if not char_id and req.rubrik == "characters":
        char_id = ProjectManager.sanitize_name(req.asset_name.split("_")[0])

    if char_id and req.rubrik == "characters":
        char_data = proj_mgr.get_character(req.project_name, char_id)

    seed = req.seed if (req.seed is not None and req.seed > 0) else random.randint(1, 2147483647)
    
    # Inherit master seed if user selected character reference and didn't specify seed
    if char_data and req.use_character_reference and (req.seed is None or req.seed <= 0):
        if char_data.get("seed", -1) > 0:
            seed = char_data["seed"]

    persp_data = persp_mgr.get_perspective(req.perspective)

    # Prompt synthesis: If character exists, anchor with base character description
    effective_prompt = req.prompt
    if char_data and req.use_character_reference:
        base_p = char_data.get("base_prompt", "")
        if base_p and base_p.lower() not in effective_prompt.lower():
            effective_prompt = f"{base_p}, {effective_prompt}"

    if req.perspective == "portrait":
        # Remove contradictory full-body tokens that confuse diffusion models into collage sheets
        import re
        for bad_token in ["full body view sprite", "full body view", "full body", "feet visible", "standing full length", "standing pose"]:
            effective_prompt = re.sub(re.escape(bad_token), "", effective_prompt, flags=re.IGNORECASE)

    # 1. Run module prompt prepare hook
    context = {
        "project": req.project_name,
        "rubrik": req.rubrik,
        "category": req.rubrik,
        "asset_name": req.asset_name,
        "character_id": char_id,
        "character_name": req.character_name or (char_data.get("name") if char_data else None),
        "perspective": req.perspective,
        "action": req.action,
        "steps": req.steps_count,
        "width": req.width,
        "height": req.height,
        "fps": req.fps,
        "seed": seed,
        "positive_prompt": effective_prompt,
        "negative_prompt": req.negative_prompt or "",
        "palette_mode": req.palette_mode
    }
    context = mod_mgr.run_prompt_prepare(context)

    # Ensure negative prompt always contains anti-sheet & anti-collage safeguards
    anti_sheet_neg = (
        "multiple characters, multiple views, character sheet, expressions sheet, "
        "portrait sheet, collage, montage, side by side, extra heads, duplicate heads, "
        "cloned face, border avatars, icons, split view, multi-panel"
    )
    if req.perspective == "portrait":
        anti_sheet_neg += ", full body, feet, shoes, legs, standing full length"

    current_neg = context.get("negative_prompt", "")
    if "multiple characters" not in current_neg:
        context["negative_prompt"] = f"{anti_sheet_neg}, {current_neg}".strip(", ")

    # 2. Check ComfyUI or fallback to mock demo if requested or offline
    # 2. Directional suite configuration
    is_suite = req.direction in ("8_directional", "4_cardinal", "isometric_4")
    if req.direction == "8_directional":
        active_directions = persp_mgr.ORDER_8_WAY
    elif req.direction == "4_cardinal":
        active_directions = persp_mgr.ORDER_4_CARDINAL
    elif req.direction == "isometric_4":
        active_directions = persp_mgr.ORDER_ISOMETRIC_4
    else:
        active_directions = [req.direction or "S"]

    # Chroma key color parsing
    parsed_bg_color = None
    if req.chroma_color:
        c = req.chroma_color.strip().lstrip("#")
        if len(c) == 6:
            try:
                parsed_bg_color = (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
            except Exception:
                parsed_bg_color = None

    comfy_status = comfy_client.check_connection()
    use_mock = req.mock_demo or (not comfy_status.get("online", False))

    # ComfyUI preparation if not using mock
    workflow = None
    latent_w = 512
    latent_h = 512
    effective_cfg = req.cfg
    effective_sampler = req.sampler_name
    effective_scheduler = req.scheduler
    master_ref_bytes: Optional[bytes] = None

    if not use_mock:
        wf_path = WORKFLOWS_DIR / (req.workflow_name or "sprite_sheet_generator.json")
        if not wf_path.exists():
            wf_path = WORKFLOWS_DIR / "pixel_asset_single.json"

        with open(wf_path, "r", encoding="utf-8") as f:
            workflow_template = json.load(f)

        workflow = mod_mgr.run_workflow_prepare(workflow_template, context)
        is_anima = bool(req.unet and "anima" in req.unet.lower())

        if req.perspective == "portrait":
            latent_w = 512
            latent_h = 768
        else:
            latent_w = 512
            latent_h = 512

        if is_anima:
            if req.cfg > 4.5:
                effective_cfg = 4.0
                logger.info(f"Auto-tuning Anima CFG from {req.cfg} to 4.0 to prevent latent saturation.")
            if not effective_sampler or effective_sampler == "euler_ancestral":
                effective_sampler = "euler"
            if not effective_scheduler or effective_scheduler == "karras":
                effective_scheduler = "simple"

        if char_id and req.rubrik == "characters" and req.use_character_reference:
            c_dir = proj_mgr.get_character_dir(req.project_name, char_id)
            m_path = c_dir / "master_reference.png"
            if m_path.exists() and m_path.stat().st_size > 30000:
                try:
                    with open(m_path, "rb") as mf:
                        master_ref_bytes = mf.read()
                    logger.info(f"Loaded master reference for {char_id} ({len(master_ref_bytes)} bytes)")
                except Exception as e:
                    logger.warning(f"Could not read master reference: {e}")

    def generate_direction_frames(d: str) -> List[Image.Image]:
        dir_cue = persp_mgr.get_direction_prompt(req.perspective, d)
        if use_mock:
            d_frames = []
            for step_idx in range(req.steps_count):
                frame = create_mock_sprite_frame(
                    width=req.width,
                    height=req.height,
                    perspective=req.perspective,
                    action=req.action,
                    step_idx=step_idx,
                    total_steps=req.steps_count,
                    asset_name=req.asset_name,
                    direction=d
                )
                d_frames.append(frame)
            return d_frames

        raw_frames: List[Image.Image] = []
        last_frame_bytes: Optional[bytes] = None

        for step_i in range(req.steps_count):
            step_cue = get_step_cue(req.action, step_i, req.steps_count, req.perspective)
            cue_parts = [context['positive_prompt']]
            if dir_cue:
                cue_parts.append(dir_cue)
            if step_cue:
                cue_parts.append(step_cue)
            if step_i > 0:
                cue_parts.append("consistent character, identical clothes and style")
            frame_prompt = ", ".join(cue_parts)

            ref_comfy_name = None
            frame_denoise = 1.0

            if step_i == 0:
                if master_ref_bytes:
                    ref_comfy_name = comfy_client.upload_image(master_ref_bytes, filename=f"master_ref_{char_id}.png")
                    frame_denoise = 0.50
            else:
                if last_frame_bytes:
                    ref_comfy_name = comfy_client.upload_image(last_frame_bytes, filename=f"frame_ref_{step_i - 1}.png")
                    frame_denoise = 0.38

            configured_wf = comfy_client.inject_parameters(
                workflow=workflow,
                positive_prompt=frame_prompt,
                negative_prompt=context["negative_prompt"],
                width=latent_w,
                height=latent_h,
                seed=seed + (step_i * 7 if step_i > 0 else 0),
                steps=req.steps,
                cfg=effective_cfg,
                checkpoint=req.checkpoint,
                unet=req.unet,
                lora=req.lora,
                lora_strength=req.lora_strength,
                vae=req.vae,
                sampler_name=effective_sampler,
                scheduler=effective_scheduler,
                reference_image=ref_comfy_name,
                denoise=frame_denoise
            )

            prompt_id = comfy_client.queue_prompt(configured_wf)
            image_outputs = comfy_client.wait_for_completion(prompt_id)
            if not image_outputs:
                raise RuntimeError(f"ComfyUI did not return output for frame {step_i + 1} ({d}).")

            fn, subf, ftype = image_outputs[0]
            raw_img_bytes = comfy_client.get_image_data(fn, subf, ftype)
            frame_img = SpriteProcessor.load_image(raw_img_bytes)
            raw_frames.append(frame_img)

            from io import BytesIO
            buf = BytesIO()
            frame_img.save(buf, format="PNG")
            last_frame_bytes = buf.getvalue()

        return [
            SpriteProcessor.resize_sprite(rf, req.width, req.height, mode=req.scaling_mode)
            for rf in raw_frames
        ]

    # 3. Generate or mirror frames for all active directions
    directional_frames: Dict[str, List[Image.Image]] = {}
    for d in active_directions:
        dir_meta = persp_mgr.get_direction(d)
        mirror_src = dir_meta.get("mirror_source") if dir_meta else None

        if req.mirror_symmetry and mirror_src and mirror_src in directional_frames:
            logger.info(f"Auto-mirroring direction {d} horizontally from {mirror_src} (saving generation time).")
            directional_frames[d] = [
                SpriteProcessor.mirror_frame(f) for f in directional_frames[mirror_src]
            ]
        else:
            logger.info(f"Generating frames for direction {d} ({req.action})...")
            try:
                d_frames = generate_direction_frames(d)
            except Exception as e:
                logger.error(f"Generation for direction {d} failed: {e}. Falling back to demo preview.")
                d_frames = [
                    create_mock_sprite_frame(
                        width=req.width,
                        height=req.height,
                        perspective=req.perspective,
                        action=req.action,
                        step_idx=step_idx,
                        total_steps=req.steps_count,
                        asset_name=req.asset_name,
                        direction=d
                    )
                    for step_idx in range(req.steps_count)
                ]
            d_frames = mod_mgr.run_postprocess(d_frames, context)
            directional_frames[d] = d_frames

    # 4. Save into structured project directory
    metadata_payload = {
        "perspective": req.perspective,
        "perspective_name": persp_data.get("name", req.perspective),
        "action": req.action,
        "steps_count": req.steps_count,
        "direction": req.direction,
        "mirror_symmetry": req.mirror_symmetry,
        "resolution": {"width": req.width, "height": req.height},
        "scaling_mode": req.scaling_mode,
        "positive_prompt": context["positive_prompt"],
        "negative_prompt": context["negative_prompt"],
        "seed": seed,
        "is_mock": use_mock,
        "workflow": req.workflow_name,
        "checkpoint": req.checkpoint,
        "unet": req.unet,
        "lora": req.lora,
        "lora_strength": req.lora_strength,
        "vae": req.vae,
        "sampler_name": req.sampler_name,
        "scheduler": req.scheduler,
        "chroma_color": req.chroma_color,
        "chroma_tolerance": req.chroma_tolerance
    }

    if is_suite and (req.rubrik == "characters" or char_id):
        c_id = char_id or ProjectManager.sanitize_name(req.asset_name)
        c_name = req.character_name or (char_data.get("name") if char_data else c_id.replace("_", " ").title())
        result = proj_mgr.save_character_directional_suite(
            project_name=req.project_name,
            character_id=c_id,
            character_name=c_name,
            action=req.action,
            directional_frames=directional_frames,
            metadata=metadata_payload,
            fps=req.fps,
            make_transparent=req.remove_background,
            directions_order=active_directions,
            set_as_master=req.set_as_master,
            bg_color=parsed_bg_color,
            tolerance=req.chroma_tolerance
        )
        return {"status": "success", "asset": result}

    # Single animation fallback
    primary_frames = directional_frames[active_directions[0]]

    if req.rubrik == "characters" or char_id:
        c_id = char_id or ProjectManager.sanitize_name(req.asset_name)
        c_name = req.character_name or (char_data.get("name") if char_data else c_id.replace("_", " ").title())
        result = proj_mgr.save_character_animation(
            project_name=req.project_name,
            character_id=c_id,
            character_name=c_name,
            action=req.action,
            frames=primary_frames,
            metadata=metadata_payload,
            fps=req.fps,
            make_transparent=req.remove_background,
            set_as_master=req.set_as_master,
            bg_color=parsed_bg_color,
            tolerance=req.chroma_tolerance
        )
    else:
        result = proj_mgr.save_asset(
            project_name=req.project_name,
            rubrik=req.rubrik,
            asset_name=req.asset_name,
            frames=primary_frames,
            metadata=metadata_payload,
            fps=req.fps,
            make_transparent=req.remove_background,
            bg_color=parsed_bg_color,
            tolerance=req.chroma_tolerance
        )

    return {"status": "success", "asset": result}



if __name__ == "__main__":
    import socket
    server_cfg = cfg.get("server", {})
    host = server_cfg.get("host", "127.0.0.1")
    desired_port = server_cfg.get("port", 7865)

    def find_free_port(start_port: int, max_attempts: int = 10) -> int:
        for p in range(start_port, start_port + max_attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((host, p)) != 0:
                    return p
        return start_port

    port = find_free_port(desired_port)
    print(f"\n========================================================", flush=True)
    print(f"  GameAssetGenerator Studio ({__version__}) starting on http://{host}:{port}", flush=True)
    print(f"========================================================\n", flush=True)
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        access_log=False,
        log_level="warning"
    )


