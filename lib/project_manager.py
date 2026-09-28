"""
Project & Asset Manager
Manages project hierarchies in the output folder:
- output/<project_name>/<rubrik>/<asset_name>/ (General assets: items, props, tilesets, etc.)
- output/<project_name>/characters/<character_id>/ (Grouped characters with master reference and animations)
  ├── master_reference.png
  ├── character.json
  └── animations/
      ├── idle/ (frames, spritesheet, preview.gif, metadata.json)
      ├── walk/
      ├── sit/
      └── jump/
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

from .sprite_processor import SpriteProcessor


class ProjectManager:
    def __init__(self, output_base_dir: Optional[Path] = None):
        self.base_dir = output_base_dir or (Path(__file__).resolve().parent.parent / "output")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitizes project, character or asset names for safe filesystem use."""
        cleaned = re.sub(r"[^\w\-_]", "_", name.strip())
        return cleaned.lower() if cleaned else "unnamed_asset"

    def get_project_dir(self, project_name: str) -> Path:
        sanitized = self.sanitize_name(project_name)
        p_dir = self.base_dir / sanitized
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir

    def get_rubrik_dir(self, project_name: str, rubrik: str) -> Path:
        p_dir = self.get_project_dir(project_name)
        sanitized_rubrik = self.sanitize_name(rubrik)
        r_dir = p_dir / sanitized_rubrik
        r_dir.mkdir(parents=True, exist_ok=True)
        return r_dir

    def get_asset_dir(self, project_name: str, rubrik: str, asset_name: str) -> Path:
        r_dir = self.get_rubrik_dir(project_name, rubrik)
        sanitized_asset = self.sanitize_name(asset_name)
        a_dir = r_dir / sanitized_asset
        a_dir.mkdir(parents=True, exist_ok=True)
        return a_dir

    # -------------------------------------------------------------
    # Character Grouping Operations
    # -------------------------------------------------------------
    def get_character_dir(self, project_name: str, character_id: str) -> Path:
        char_root = self.get_rubrik_dir(project_name, "characters")
        c_dir = char_root / self.sanitize_name(character_id)
        c_dir.mkdir(parents=True, exist_ok=True)
        (c_dir / "animations").mkdir(parents=True, exist_ok=True)
        return c_dir

    def list_characters(self, project_name: str) -> List[Dict[str, Any]]:
        """Lists all character entities in a project with their animation suites."""
        char_root = self.base_dir / self.sanitize_name(project_name) / "characters"
        if not char_root.exists():
            return []

        characters = []
        for c_dir in char_root.iterdir():
            if c_dir.is_dir() and not c_dir.name.startswith("."):
                char_file = c_dir / "character.json"
                char_data = {}
                if char_file.exists():
                    try:
                        with open(char_file, "r", encoding="utf-8") as f:
                            char_data = json.load(f)
                    except Exception:
                        pass

                master_img_path = c_dir / "master_reference.png"
                has_master = master_img_path.exists()

                # Scan available animations
                anim_dir = c_dir / "animations"
                anims = {}
                if anim_dir.exists():
                    for a_dir in anim_dir.iterdir():
                        if a_dir.is_dir():
                            anims[a_dir.name] = {
                                "action": a_dir.name,
                                "preview_gif": f"/output/{project_name}/characters/{c_dir.name}/animations/{a_dir.name}/preview.gif",
                                "spritesheet": f"/output/{project_name}/characters/{c_dir.name}/animations/{a_dir.name}/spritesheet.png"
                            }

                characters.append({
                    "character_id": c_dir.name,
                    "name": char_data.get("name", c_dir.name.replace("_", " ").title()),
                    "project": project_name,
                    "perspective": char_data.get("perspective", "side_view"),
                    "base_prompt": char_data.get("base_prompt", ""),
                    "seed": char_data.get("seed", -1),
                    "style_id": char_data.get("style_id", ""),
                    "has_master_reference": has_master,
                    "master_reference_url": f"/output/{project_name}/characters/{c_dir.name}/master_reference.png" if has_master else "",
                    "animations_count": len(anims),
                    "animations": anims,
                    "created_at": char_data.get("created_at", "")
                })

        return sorted(characters, key=lambda c: c["name"])

    def get_character(self, project_name: str, character_id: str) -> Optional[Dict[str, Any]]:
        c_dir = self.base_dir / self.sanitize_name(project_name) / "characters" / self.sanitize_name(character_id)
        if not c_dir.exists():
            return None
        char_file = c_dir / "character.json"
        if char_file.exists():
            try:
                with open(char_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def save_character_animation(
        self,
        project_name: str,
        character_id: str,
        character_name: str,
        action: str,
        frames: List[Image.Image],
        metadata: Dict[str, Any],
        fps: int = 8,
        make_transparent: bool = True,
        set_as_master: bool = False
    ) -> Dict[str, Any]:
        """
        Saves animation under the character group:
        output/<project>/characters/<character_id>/animations/<action>/
        And optionally updates/creates master_reference.png and character.json.
        """
        c_dir = self.get_character_dir(project_name, character_id)
        anim_dir = c_dir / "animations" / self.sanitize_name(action)
        frames_dir = anim_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        processed_frames = []
        for i, frame in enumerate(frames):
            img = frame
            if make_transparent:
                img = SpriteProcessor.make_transparent(img)
            processed_frames.append(img)
            frame_path = frames_dir / f"frame_{i+1:02d}.png"
            img.save(frame_path, format="PNG")

        # Spritesheet
        spritesheet = SpriteProcessor.pack_spritesheet(processed_frames)
        sheet_path = anim_dir / "spritesheet.png"
        spritesheet.save(sheet_path, format="PNG")

        # Previews
        gif_path = anim_dir / "preview.gif"
        webp_path = anim_dir / "preview.webp"
        SpriteProcessor.create_animated_gif(processed_frames, gif_path, fps=fps)
        SpriteProcessor.create_animated_webp(processed_frames, webp_path, fps=fps)

        # Master reference image
        master_img_path = c_dir / "master_reference.png"
        if set_as_master or not master_img_path.exists():
            # Use first frame as master reference image
            processed_frames[0].save(master_img_path, format="PNG")

        # Update character.json
        char_file = c_dir / "character.json"
        char_data = {}
        if char_file.exists():
            try:
                with open(char_file, "r", encoding="utf-8") as f:
                    char_data = json.load(f)
            except Exception:
                pass

        if not char_data:
            char_data = {
                "character_id": self.sanitize_name(character_id),
                "name": character_name or character_id.replace("_", " ").title(),
                "project": project_name,
                "perspective": metadata.get("perspective", "side_view"),
                "base_prompt": metadata.get("positive_prompt", ""),
                "base_negative_prompt": metadata.get("negative_prompt", ""),
                "seed": metadata.get("seed", -1),
                "style_id": metadata.get("style_id", ""),
                "created_at": datetime.now().isoformat(),
                "animations": {}
            }

        char_data.setdefault("animations", {})
        char_data["animations"][action] = {
            "action": action,
            "total_frames": len(processed_frames),
            "fps": fps,
            "paths": {
                "spritesheet": f"/output/{project_name}/characters/{c_dir.name}/animations/{action}/spritesheet.png",
                "preview_gif": f"/output/{project_name}/characters/{c_dir.name}/animations/{action}/preview.gif",
                "preview_webp": f"/output/{project_name}/characters/{c_dir.name}/animations/{action}/preview.webp"
            },
            "updated_at": datetime.now().isoformat()
        }

        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(char_data, f, indent=2, ensure_ascii=False)

        # Engine metadata for this animation
        frame_w, frame_h = processed_frames[0].size
        engine_meta = SpriteProcessor.generate_engine_metadata(
            asset_name=f"{character_id}_{action}",
            category="characters",
            perspective=metadata.get("perspective", "side_view"),
            action=action,
            frame_width=frame_w,
            frame_height=frame_h,
            fps=fps,
            frames_count=len(processed_frames),
            spritesheet_filename="spritesheet.png"
        )

        full_metadata = {
            **metadata,
            "created_at": datetime.now().isoformat(),
            "project": project_name,
            "character_id": c_dir.name,
            "character_name": char_data.get("name", ""),
            "rubrik": "characters",
            "action": action,
            "asset_name": f"{c_dir.name}_{action}",
            "total_frames": len(processed_frames),
            "frame_dimensions": {"width": frame_w, "height": frame_h},
            "fps": fps,
            "paths": {
                "asset_folder": str(anim_dir),
                "master_reference": f"/output/{project_name}/characters/{c_dir.name}/master_reference.png",
                "spritesheet": f"/output/{project_name}/characters/{c_dir.name}/animations/{action}/spritesheet.png",
                "preview_gif": f"/output/{project_name}/characters/{c_dir.name}/animations/{action}/preview.gif",
                "preview_webp": f"/output/{project_name}/characters/{c_dir.name}/animations/{action}/preview.webp",
                "frames": [
                    f"/output/{project_name}/characters/{c_dir.name}/animations/{action}/frames/frame_{i+1:02d}.png"
                    for i in range(len(processed_frames))
                ]
            },
            "engine_export": engine_meta
        }

        with open(anim_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(full_metadata, f, indent=2, ensure_ascii=False)

        return full_metadata

    # -------------------------------------------------------------
    # General Asset Operations
    # -------------------------------------------------------------
    def list_projects(self) -> List[str]:
        if not self.base_dir.exists():
            return []
        return sorted([
            d.name for d in self.base_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ])

    def list_rubriken(self, project_name: str) -> List[str]:
        p_dir = self.base_dir / self.sanitize_name(project_name)
        if not p_dir.exists():
            return []
        return sorted([
            d.name for d in p_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ])

    def list_assets(self, project_name: str, rubrik: Optional[str] = None) -> List[Dict[str, Any]]:
        p_dir = self.base_dir / self.sanitize_name(project_name)
        if not p_dir.exists():
            return []

        results = []
        rubrik_dirs = [p_dir / self.sanitize_name(rubrik)] if rubrik else [
            d for d in p_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]

        for r_dir in rubrik_dirs:
            if not r_dir.exists():
                continue

            # Special inspection for characters rubrik to list grouped animations
            if r_dir.name == "characters":
                for c_dir in r_dir.iterdir():
                    if c_dir.is_dir():
                        anims_dir = c_dir / "animations"
                        if anims_dir.exists():
                            for a_dir in anims_dir.iterdir():
                                if a_dir.is_dir():
                                    meta_path = a_dir / "metadata.json"
                                    meta = {}
                                    if meta_path.exists():
                                        try:
                                            with open(meta_path, "r", encoding="utf-8") as f:
                                                meta = json.load(f)
                                        except Exception:
                                            pass
                                    results.append({
                                        "project": project_name,
                                        "rubrik": "characters",
                                        "character_id": c_dir.name,
                                        "asset_name": f"{c_dir.name}_{a_dir.name}",
                                        "action": a_dir.name,
                                        "thumbnail_path": f"/output/{project_name}/characters/{c_dir.name}/animations/{a_dir.name}/preview.gif",
                                        "metadata": meta
                                    })
                        else:
                            # Standard single asset fallback if not using new structure
                            meta_path = c_dir / "metadata.json"
                            meta = {}
                            if meta_path.exists():
                                try:
                                    with open(meta_path, "r", encoding="utf-8") as f:
                                        meta = json.load(f)
                                except Exception:
                                    pass
                            results.append({
                                "project": project_name,
                                "rubrik": "characters",
                                "asset_name": c_dir.name,
                                "thumbnail_path": f"/output/{project_name}/characters/{c_dir.name}/preview.gif",
                                "metadata": meta
                            })
            else:
                for a_dir in r_dir.iterdir():
                    if a_dir.is_dir():
                        meta_path = a_dir / "metadata.json"
                        meta = {}
                        if meta_path.exists():
                            try:
                                with open(meta_path, "r", encoding="utf-8") as f:
                                    meta = json.load(f)
                            except Exception:
                                pass

                        preview_gif = a_dir / "preview.gif"
                        preview_png = a_dir / "spritesheet.png"

                        results.append({
                            "project": project_name,
                            "rubrik": r_dir.name,
                            "asset_name": a_dir.name,
                            "thumbnail_path": f"/output/{project_name}/{r_dir.name}/{a_dir.name}/" + (
                                "preview.gif" if preview_gif.exists() else "spritesheet.png"
                            ),
                            "metadata": meta
                        })
        return results

    def save_asset(
        self,
        project_name: str,
        rubrik: str,
        asset_name: str,
        frames: List[Image.Image],
        metadata: Dict[str, Any],
        fps: int = 8,
        make_transparent: bool = True
    ) -> Dict[str, Any]:
        """Standard save for general assets."""
        asset_dir = self.get_asset_dir(project_name, rubrik, asset_name)
        frames_dir = asset_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        processed_frames = []
        for i, frame in enumerate(frames):
            img = frame
            if make_transparent:
                img = SpriteProcessor.make_transparent(img)
            processed_frames.append(img)
            frame_path = frames_dir / f"frame_{i+1:02d}.png"
            img.save(frame_path, format="PNG")

        spritesheet = SpriteProcessor.pack_spritesheet(processed_frames)
        sheet_path = asset_dir / "spritesheet.png"
        spritesheet.save(sheet_path, format="PNG")

        gif_path = asset_dir / "preview.gif"
        webp_path = asset_dir / "preview.webp"
        SpriteProcessor.create_animated_gif(processed_frames, gif_path, fps=fps)
        SpriteProcessor.create_animated_webp(processed_frames, webp_path, fps=fps)

        frame_w, frame_h = processed_frames[0].size
        engine_meta = SpriteProcessor.generate_engine_metadata(
            asset_name=asset_name,
            category=rubrik,
            perspective=metadata.get("perspective", "side_view"),
            action=metadata.get("action", "walk"),
            frame_width=frame_w,
            frame_height=frame_h,
            fps=fps,
            frames_count=len(processed_frames),
            spritesheet_filename="spritesheet.png"
        )

        full_metadata = {
            **metadata,
            "created_at": datetime.now().isoformat(),
            "project": project_name,
            "rubrik": rubrik,
            "asset_name": asset_name,
            "total_frames": len(processed_frames),
            "frame_dimensions": {"width": frame_w, "height": frame_h},
            "fps": fps,
            "paths": {
                "asset_folder": str(asset_dir),
                "spritesheet": f"/output/{project_name}/{rubrik}/{asset_name}/spritesheet.png",
                "preview_gif": f"/output/{project_name}/{rubrik}/{asset_name}/preview.gif",
                "preview_webp": f"/output/{project_name}/{rubrik}/{asset_name}/preview.webp",
                "frames": [
                    f"/output/{project_name}/{rubrik}/{asset_name}/frames/frame_{i+1:02d}.png"
                    for i in range(len(processed_frames))
                ]
            },
            "engine_export": engine_meta
        }

        with open(asset_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(full_metadata, f, indent=2, ensure_ascii=False)

        return full_metadata
