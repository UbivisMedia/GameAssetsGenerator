"""
Perspective Manager
Handles perspective definitions, angle parameters, and spatial prompt generation
for Side-View, Top-Down, Isometric, and Portrait (jRPG) game assets.
"""

from typing import Any, Dict, List, Optional


class PerspectiveManager:
    def __init__(self, perspectives: List[Dict[str, Any]]):
        self._perspectives = {p["id"]: p for p in perspectives}

    def list_perspectives(self) -> List[Dict[str, Any]]:
        return list(self._perspectives.values())

    def get_perspective(self, perspective_id: str) -> Dict[str, Any]:
        if perspective_id in self._perspectives:
            return self._perspectives[perspective_id]
        # Default fallback
        return {
            "id": "side_view",
            "name": "Seitenansicht (Side-View)",
            "prompt_prefix": "side view 2D game asset, horizontal profile",
            "negative_prompt": "top-down, bird's eye, isometric, 3d tilt"
        }

    def format_perspective_prompt(self, perspective_id: str, base_prompt: str) -> str:
        """Prefaces prompt with strong perspective tokens."""
        persp = self.get_perspective(perspective_id)
        prefix = persp.get("prompt_prefix", "")
        if prefix:
            return f"{prefix}, {base_prompt}"
        return base_prompt

    def get_negative_prompt(self, perspective_id: str, base_negative: str = "") -> str:
        """Combines base negative prompt with perspective-counteracting tokens."""
        persp = self.get_perspective(perspective_id)
        persp_neg = persp.get("negative_prompt", "")
        if base_negative and persp_neg:
            return f"{persp_neg}, {base_negative}"
        return persp_neg or base_negative

    def get_recommended_grid(self, perspective_id: str, width: int, height: int) -> Dict[str, Any]:
        """Returns coordinate / grid geometry advice for the perspective."""
        if perspective_id == "isometric":
            return {
                "type": "dimetric_2_to_1",
                "tile_width": width,
                "tile_height": width // 2 if width > 0 else height // 2,
                "angle_degrees": 30.0,
                "notes": "Classic 2:1 isometric diamond projection"
            }
        elif perspective_id == "top_down":
            return {
                "type": "orthogonal_square",
                "tile_width": width,
                "tile_height": height,
                "angle_degrees": 90.0,
                "notes": "Square top-down orthogonal grid"
            }
        elif perspective_id == "portrait":
            return {
                "type": "dialogue_bust",
                "tile_width": width,
                "tile_height": height,
                "angle_degrees": 0.0,
                "notes": "Character dialogue bust / face portrait"
            }
        else: # side_view
            return {
                "type": "planar_side_scroller",
                "tile_width": width,
                "tile_height": height,
                "angle_degrees": 0.0,
                "notes": "Flat ground baseline alignment"
            }
