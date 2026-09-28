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

    # -------------------------------------------------------------
    # 8-Directional Movement Definitions & Spatial Prompts
    # -------------------------------------------------------------
    DIRECTIONS = {
        "S": {
            "id": "S",
            "name": "South (Down / Front)",
            "angle": 180,
            "badge": "Front",
            "prompt_top_down": "facing camera, front view, moving downwards towards the viewer",
            "prompt_isometric": "facing down along isometric axis, front view towards viewer",
            "mirror_source": None
        },
        "SW": {
            "id": "SW",
            "name": "South-West (Down-Left)",
            "angle": 225,
            "badge": "Down-Left",
            "prompt_top_down": "facing diagonally down-left towards camera, three-quarter front-left view",
            "prompt_isometric": "isometric view facing down-left along 30-degree isometric grid axis",
            "mirror_source": None
        },
        "W": {
            "id": "W",
            "name": "West (Left Profile)",
            "angle": 270,
            "badge": "Left",
            "prompt_top_down": "facing completely leftwards, left side profile view, horizontal movement to the left",
            "prompt_isometric": "facing left profile along isometric ground plane",
            "mirror_source": None
        },
        "NW": {
            "id": "NW",
            "name": "North-West (Up-Left)",
            "angle": 315,
            "badge": "Up-Left",
            "prompt_top_down": "facing diagonally away towards upper-left, three-quarter back-left view, back visible",
            "prompt_isometric": "isometric view facing away up-left along 30-degree isometric grid axis, back visible",
            "mirror_source": None
        },
        "N": {
            "id": "N",
            "name": "North (Up / Back)",
            "angle": 0,
            "badge": "Back",
            "prompt_top_down": "rear view, back facing camera, moving upwards away from the viewer, back of head",
            "prompt_isometric": "rear view facing upwards away along isometric axis, back facing viewer",
            "mirror_source": None
        },
        "NE": {
            "id": "NE",
            "name": "North-East (Up-Right)",
            "angle": 45,
            "badge": "Up-Right",
            "prompt_top_down": "facing diagonally away towards upper-right, three-quarter back-right view, back visible",
            "prompt_isometric": "isometric view facing away up-right along 30-degree isometric grid axis, back visible",
            "mirror_source": "NW"
        },
        "E": {
            "id": "E",
            "name": "East (Right Profile)",
            "angle": 90,
            "badge": "Right",
            "prompt_top_down": "facing completely rightwards, right side profile view, horizontal movement to the right",
            "prompt_isometric": "facing right profile along isometric ground plane",
            "mirror_source": "W"
        },
        "SE": {
            "id": "SE",
            "name": "South-East (Down-Right)",
            "angle": 135,
            "badge": "Down-Right",
            "prompt_top_down": "facing diagonally down-right towards camera, three-quarter front-right view",
            "prompt_isometric": "isometric view facing down-right along 30-degree isometric grid axis",
            "mirror_source": "SW"
        }
    }

    ORDER_8_WAY = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
    ORDER_4_CARDINAL = ["S", "W", "N", "E"]
    ORDER_ISOMETRIC_4 = ["SE", "SW", "NW", "NE"]

    def list_directions(self) -> List[Dict[str, Any]]:
        return [self.DIRECTIONS[k] for k in self.ORDER_8_WAY]

    def get_direction(self, dir_id: str) -> Optional[Dict[str, Any]]:
        return self.DIRECTIONS.get(dir_id.upper())

    def get_direction_prompt(self, dir_id: str, perspective_id: str = "top_down") -> str:
        d = self.get_direction(dir_id)
        if not d:
            return ""
        if perspective_id == "isometric":
            return d.get("prompt_isometric", d.get("prompt_top_down", ""))
        return d.get("prompt_top_down", "")
