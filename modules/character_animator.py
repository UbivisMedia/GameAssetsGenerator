"""
Character Animator Module
Maintains animation pose consistency and movement step instructions for characters.
"""

from typing import Any, Dict
from lib.module_interface import BaseAssetModule


class CharacterAnimatorModule(BaseAssetModule):
    module_id = "character_animator"
    name = "Character Animation Assistant"
    version = "1.0.0"
    description = "Optimizes prompts for animation phases (walk, sit, jump) ensuring consistent character silhouettes."
    author = "GameAssetGenerator Core"
    enabled = True

    def on_prompt_prepare(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Injects movement and pose consistency keywords if category is character."""
        category = context.get("category", "")
        action = context.get("action", "")
        steps = context.get("steps", 1)

        if category == "characters" and action:
            pos = context.get("positive_prompt", "")
            action_tags = {
                "walk": "clean walk cycle sequence, grounded feet, dynamic stepping pose",
                "run": "high speed running stride, aerodynamic forward tilt, motion silhouette",
                "sit": "sitting animation sequence, bending knees downward, relaxed seated posture",
                "jump": "jumping arc, vertical lift, airborne knees flexed, gravity impact",
                "idle": "subtle breathing stance, resting ready pose, relaxed arms",
                "attack": "weapon strike action frame, kinetic attack slash, anticipation pose",
                "talk": "dialogue mouth speaking and closing, eye blinking, expressive speech portrait frames"
            }
            extra = action_tags.get(action.lower(), f"{action} animation phase")
            context["positive_prompt"] = f"{pos}, {extra}, consistent character design, matching clothing and colors"

            neg = context.get("negative_prompt", "")
            context["negative_prompt"] = f"{neg}, changing character faces, morphing anatomy, differing outfits"

        return context
