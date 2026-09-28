"""
Sprite Processor
Handles resizing, transparency extraction, sprite-sheet slicing,
spritesheet packing, animated GIF/WebP creation, and engine metadata generation.
"""

import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageChops, ImageOps


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
        bg_color: Optional[Tuple[int, int, int]] = (255, 255, 255),
        tolerance: int = 35
    ) -> Image.Image:
        """
        Removes background starting from image borders (flood fill from corners/edges)
        so that white/light elements inside the character (e.g. eyes, teeth, white clothes)
        are protected and NEVER accidentally erased.
        Also safeguards against wiping out the entire image.
        """
        img = image.convert("RGBA")
        w, h = img.size
        pixels = img.load()

        if bg_color is None:
            corners = [pixels[0, 0], pixels[w - 1, 0], pixels[0, h - 1], pixels[w - 1, h - 1]]
            avg_r = int(sum(c[0] for c in corners) / 4)
            avg_g = int(sum(c[1] for c in corners) / 4)
            avg_b = int(sum(c[2] for c in corners) / 4)
            tr, tg, tb = avg_r, avg_g, avg_b
        else:
            tr, tg, tb = bg_color

        from collections import deque
        visited = bytearray(w * h)
        queue = deque()

        # Seed from all 4 borders
        for x in range(w):
            for y in (0, h - 1):
                idx = y * w + x
                if not visited[idx]:
                    r, g, b, a = pixels[x, y]
                    if max(abs(r - tr), abs(g - tg), abs(b - tb)) <= tolerance + 15:
                        visited[idx] = 1
                        queue.append((x, y))

        for y in range(h):
            for x in (0, w - 1):
                idx = y * w + x
                if not visited[idx]:
                    r, g, b, a = pixels[x, y]
                    if max(abs(r - tr), abs(g - tg), abs(b - tb)) <= tolerance + 15:
                        visited[idx] = 1
                        queue.append((x, y))

        transparent_count = 0
        while queue:
            cx, cy = queue.popleft()
            r, g, b, a = pixels[cx, cy]
            diff = max(abs(r - tr), abs(g - tg), abs(b - tb))

            if diff <= tolerance:
                pixels[cx, cy] = (r, g, b, 0)
                transparent_count += 1
            elif diff <= tolerance + 15:
                alpha = int(a * ((diff - tolerance) / 15.0))
                pixels[cx, cy] = (r, g, b, alpha)

            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h:
                    nidx = ny * w + nx
                    if not visited[nidx]:
                        visited[nidx] = 1
                        nr, ng, nb, _ = pixels[nx, ny]
                        if max(abs(nr - tr), abs(ng - tg), abs(nb - tb)) <= tolerance + 15:
                            queue.append((nx, ny))

        # Safeguard: if flood fill erased > 95% of pixels, keep original to avoid blank frames
        if transparent_count >= w * h * 0.95:
            return image.convert("RGBA")

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
    def mirror_frame(cls, frame: Image.Image) -> Image.Image:
        """Horizontally flips a sprite frame for symmetrical opposite angles."""
        return ImageOps.mirror(frame)

    @classmethod
    def pack_directional_spritesheet(
        cls,
        directional_frames: Dict[str, List[Image.Image]],
        directions_order: Optional[List[str]] = None,
        padding: int = 0
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """
        Packs an 8-way or 4-way multi-directional animation into a standard multi-row spritesheet.
        Each row represents one direction, and each column represents a frame of that direction.
        Returns (sheet_image, engine_export_metadata).
        """
        if not directional_frames:
            raise ValueError("No directional frames provided.")

        order = directions_order or list(directional_frames.keys())
        active_dirs = [d for d in order if d in directional_frames and directional_frames[d]]
        if not active_dirs:
            raise ValueError("No valid directions found in directional frames.")

        max_frames = max(len(directional_frames[d]) for d in active_dirs)
        sample_frame = directional_frames[active_dirs[0]][0]
        frame_w, frame_h = sample_frame.size

        sheet_w = max_frames * frame_w + (max_frames - 1) * padding
        sheet_h = len(active_dirs) * frame_h + (len(active_dirs) - 1) * padding

        sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
        frames_meta = []
        animations_meta = {}

        for row_idx, d in enumerate(active_dirs):
            dir_frames = directional_frames[d]
            dir_indices = []
            for col_idx, frame in enumerate(dir_frames):
                x = col_idx * (frame_w + padding)
                y = row_idx * (frame_h + padding)
                sheet.paste(frame, (x, y), mask=frame)

                frame_name = f"dir_{d}_frame_{col_idx+1:02d}.png"
                global_idx = row_idx * max_frames + col_idx
                dir_indices.append(global_idx)

                frames_meta.append({
                    "filename": frame_name,
                    "direction": d,
                    "frame_idx": col_idx,
                    "frame": {"x": x, "y": y, "w": frame_w, "h": frame_h},
                    "sourceSize": {"w": frame_w, "h": frame_h}
                })

            animations_meta[d] = {
                "direction": d,
                "frames": dir_indices,
                "count": len(dir_frames)
            }

        metadata = {
            "directions": active_dirs,
            "frames_per_direction": max_frames,
            "frame_size": {"width": frame_w, "height": frame_h},
            "rows": len(active_dirs),
            "columns": max_frames,
            "frames": frames_meta,
            "animations": animations_meta
        }

        return sheet, metadata

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

    @classmethod
    def generate_normal_map(
        cls,
        image: Image.Image,
        strength: float = 2.0,
        invert_y: bool = False
    ) -> Image.Image:
        """
        Bakes a tangent-space 2D normal map from a sprite frame or spritesheet using
        a 3x3 Sobel gradient filter. Compatible with Godot (CanvasTexture/Light2D)
        and Unity (URP 2D Lights).
        """
        import numpy as np

        img = image.convert("RGBA")
        arr = np.array(img, dtype=np.float32)
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

        # Derive height from luminance, modulated by alpha transparency
        luminance = (0.299 * r + 0.587 * g + 0.114 * b)
        height = luminance * (a / 255.0)

        padded = np.pad(height, ((1, 1), (1, 1)), mode="edge")

        # 3x3 Sobel horizontal gradient
        dx = (
            (padded[:-2, 2:] + 2 * padded[1:-1, 2:] + padded[2:, 2:]) -
            (padded[:-2, :-2] + 2 * padded[1:-1, :-2] + padded[2:, :-2])
        ) / 8.0

        # 3x3 Sobel vertical gradient
        dy = (
            (padded[2:, :-2] + 2 * padded[2:, 1:-1] + padded[2:, 2:]) -
            (padded[:-2, :-2] + 2 * padded[:-2, 1:-1] + padded[:-2, 2:])
        ) / 8.0

        if invert_y:
            dy = -dy

        nx = -dx * (strength / 255.0 * 20.0)
        ny = -dy * (strength / 255.0 * 20.0)
        nz = np.ones_like(nx)

        length = np.sqrt(nx * nx + ny * ny + nz * nz)
        length[length == 0] = 1.0

        nx /= length
        ny /= length
        nz /= length

        # Map [-1, 1] to [0, 255] (tangent space: +Z points out of screen = light purple/blue)
        norm_r = ((nx * 0.5 + 0.5) * 255.0).clip(0, 255).astype(np.uint8)
        norm_g = ((ny * 0.5 + 0.5) * 255.0).clip(0, 255).astype(np.uint8)
        norm_b = ((nz * 0.5 + 0.5) * 255.0).clip(0, 255).astype(np.uint8)
        norm_a = a.astype(np.uint8)

        return Image.fromarray(np.stack([norm_r, norm_g, norm_b, norm_a], axis=2), mode="RGBA")

    @classmethod
    def generate_depth_map(
        cls,
        image: Image.Image,
        invert: bool = False
    ) -> Image.Image:
        """
        Generates a grayscale depth/height map from a sprite frame,
        combining luminance and alpha coverage for parallax and occlusion.
        """
        import numpy as np

        img = image.convert("RGBA")
        arr = np.array(img, dtype=np.float32)
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

        luminance = (0.299 * r + 0.587 * g + 0.114 * b)
        height = luminance * (a / 255.0)

        if invert:
            height = 255.0 - height

        d_val = height.clip(0, 255).astype(np.uint8)
        norm_a = a.astype(np.uint8)

        return Image.fromarray(np.stack([d_val, d_val, d_val, norm_a], axis=2), mode="RGBA")

