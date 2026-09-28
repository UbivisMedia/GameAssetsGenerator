"""
Palette Quantizer Module
Post-processing hook that reduces colors into authentic retro palettes (Pico-8, GameBoy, Endesga 32).
"""

from typing import Any, Dict, List
from PIL import Image
from lib.module_interface import BaseAssetModule


class PaletteQuantizerModule(BaseAssetModule):
    module_id = "palette_quantizer"
    name = "Retro Palette Quantizer"
    version = "1.0.0"
    description = "Optional post-processor: Restricts colors to classic retro palettes for authentic pixel-art aesthetics."
    author = "GameAssetGenerator Core"
    enabled = False

    PALETTES = {
        "pico8": [
            (0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81),
            (171, 82, 54), (95, 87, 79), (194, 195, 199), (255, 241, 232),
            (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54),
            (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170)
        ],
        "gameboy": [
            (15, 56, 15), (48, 98, 48), (139, 172, 15), (155, 188, 15)
        ]
    }

    def on_postprocess(self, frames: List[Image.Image], context: Dict[str, Any]) -> List[Image.Image]:
        palette_mode = context.get("palette_mode")
        if not palette_mode or palette_mode not in self.PALETTES:
            return frames

        palette_colors = self.PALETTES[palette_mode]
        pal_img = Image.new("P", (1, 1))
        flat_pal = []
        for rgb in palette_colors:
            flat_pal.extend(rgb)
        while len(flat_pal) < 768:
            flat_pal.extend((0, 0, 0))
        pal_img.putpalette(flat_pal)

        processed = []
        for frame in frames:
            alpha = frame.split()[-1]
            rgb_frame = frame.convert("RGB")
            quantized = rgb_frame.quantize(palette=pal_img, dither=Image.Dither.FLOYDSTEINBERG).convert("RGBA")
            quantized.putalpha(alpha)
            processed.append(quantized)

        return processed
