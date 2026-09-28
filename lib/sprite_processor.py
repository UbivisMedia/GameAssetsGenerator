"""
Sprite Processor
Handles resizing, transparency extraction, sprite-sheet slicing,
spritesheet packing, animated GIF/WebP creation, and engine metadata generation.
"""

import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageChops


class SpriteProcessor:
    RESAMPLING_MODES = {
        "nearest": Image.Resampling.NEAREST,
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
        "lanczos": Image.Resampling.LANCZOS
    }

    @classmethod
    def load_image(cls, data_or_path: Any) -> Image.Image:
        """Loads an image from bytes, BytesIO, or file path and ensures RGBA."""
        if isinstance(data_or_path, (bytes, bytearray)):
            img = Image.open(BytesIO(data_or_path))
        elif isinstance(data_or_path, (str, Path)):
            img = Image.open(data_or_path)
        elif isinstance(data_or_path, Image.Image):
            img = data_or_path
        else:
            raise ValueError(f"Unsupported image input type: {type(data_or_path)}")
        return img.convert("RGBA")

    @classmethod
    def resize_sprite(
        cls,
        image: Image.Image,
        target_width: int,
        target_height: int,
        mode: str = "nearest"
    ) -> Image.Image:
        """Resizes sprite using specified filter (nearest for pixel art)."""
        resample_filter = cls.RESAMPLING_MODES.get(mode.lower(), Image.Resampling.NEAREST)
        return image.resize((target_width, target_height), resample=resample_filter)

    @classmethod
    def make_transparent(
        cls,
        image: Image.Image,
        bg_color: Tuple[int, int, int] = (255, 255, 255),
        tolerance: int = 35
    ) -> Image.Image:
        """
        Removes solid background color (e.g. pure white or studio backdrop)
        with tolerance to produce a clean transparent PNG.
        """
        img = image.convert("RGBA")
        data = img.getdata()
        new_data = []

        tr, tg, tb = bg_color

        for item in data:
            r, g, b, a = item
            diff = max(abs(r - tr), abs(g - tg), abs(b - tb))
            if diff <= tolerance:
                # Fully transparent
                new_data.append((r, g, b, 0))
            elif diff <= tolerance + 15:
                # Feather edge
                alpha_factor = (diff - tolerance) / 15.0
                new_data.append((r, g, b, int(a * alpha_factor)))
            else:
                new_data.append(item)

        img.putdata(new_data)
        return img

    @classmethod
    def slice_strip(
        cls,
        strip_image: Image.Image,
        num_frames: int,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        scaling_mode: str = "nearest"
    ) -> List[Image.Image]:
        """
        Slices a horizontal strip image into num_frames individual sprites.
        Optionally resizes each frame to target dimensions.
        """
        strip_w, strip_h = strip_image.size
        frame_w = strip_w // num_frames
        frames = []

        for i in range(num_frames):
            box = (i * frame_w, 0, (i + 1) * frame_w, strip_h)
            frame = strip_image.crop(box)
            if target_width and target_height:
                frame = cls.resize_sprite(frame, target_width, target_height, scaling_mode)
            frames.append(frame)

        return frames

    @classmethod
    def pack_spritesheet(
        cls,
        frames: List[Image.Image],
        columns: Optional[int] = None,
        padding: int = 0
    ) -> Image.Image:
        """
        Packs a list of frames into a 2D spritesheet grid.
        Default is a single horizontal row if columns is None or equal to len(frames).
        """
        if not frames:
            raise ValueError("No frames provided to pack into spritesheet.")

        num_frames = len(frames)
        cols = columns if columns and columns > 0 else num_frames
        rows = (num_frames + cols - 1) // cols

        frame_w, frame_h = frames[0].size
        sheet_w = cols * frame_w + (cols - 1) * padding
        sheet_h = rows * frame_h + (rows - 1) * padding

        sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

        for idx, frame in enumerate(frames):
            col = idx % cols
            row = idx // cols
            x = col * (frame_w + padding)
            y = row * (frame_h + padding)
            sheet.paste(frame, (x, y), mask=frame)

        return sheet

    @classmethod
    def create_animated_gif(
        cls,
        frames: List[Image.Image],
        output_path: Path,
        fps: int = 8,
        loop: bool = True
    ) -> None:
        """Saves frames as an animated GIF with transparency."""
        if not frames:
            return
        duration_ms = max(20, int(1000 / max(1, fps)))
        
        # Convert frames for clean GIF transparency
        gif_frames = []
        for f in frames:
            alpha = f.split()[-1]
            p_img = f.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
            # Use index 255 as transparent color
            mask = Image.eval(alpha, lambda a: 255 if a < 128 else 0)
            p_img.paste(255, mask)
            gif_frames.append(p_img)

        gif_frames[0].save(
            output_path,
            save_all=True,
            append_images=gif_frames[1:],
            duration=duration_ms,
            loop=0 if loop else 1,
            transparency=255,
            disposal=2
        )

    @classmethod
    def create_animated_webp(
        cls,
        frames: List[Image.Image],
        output_path: Path,
        fps: int = 8,
        loop: bool = True
    ) -> None:
        """Saves frames as high-fidelity animated WebP with full 8-bit alpha."""
        if not frames:
            return
        duration_ms = max(20, int(1000 / max(1, fps)))
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration_ms,
            loop=0 if loop else 1,
            lossless=True
        )

    @classmethod
    def generate_engine_metadata(
        cls,
        asset_name: str,
        category: str,
        perspective: str,
        action: str,
        frame_width: int,
        frame_height: int,
        fps: int,
        frames_count: int,
        spritesheet_filename: str
    ) -> Dict[str, Any]:
        """Generates game-engine friendly metadata (Godot, Phaser, Unity)."""
        return {
            "name": asset_name,
            "category": category,
            "perspective": perspective,
            "animation": {
                "action": action,
                "fps": fps,
                "frames_count": frames_count,
                "frame_size": {"width": frame_width, "height": frame_height}
            },
            "spritesheet": {
                "file": spritesheet_filename,
                "frames": [
                    {
                        "filename": f"{asset_name}_frame_{i+1:02d}.png",
                        "frame": {"x": i * frame_width, "y": 0, "w": frame_width, "h": frame_height},
                        "rotated": False,
                        "trimmed": False,
                        "spriteSourceSize": {"x": 0, "y": 0, "w": frame_width, "h": frame_height},
                        "sourceSize": {"w": frame_width, "h": frame_height},
                        "duration": max(20, int(1000 / max(1, fps)))
                    }
                    for i in range(frames_count)
                ]
            },
            "godot_sprite_frames": {
                "animations": [
                    {
                        "name": action,
                        "speed": fps,
                        "loop": True if action in ("walk", "run", "idle") else False,
                        "frames": [i for i in range(frames_count)]
                    }
                ]
            }
        }
