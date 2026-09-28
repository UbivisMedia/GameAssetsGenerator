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
        perspective = context.get("perspective", "")

        if category == "characters" and action:
            pos = context.get("positive_prompt", "")
            action_tags = {
                "walk": "grounded feet, dynamic stepping pose",
                "run": "high speed running stride, aerodynamic forward tilt",
                "sit": "bending knees downward, relaxed seated posture",
                "jump": "jumping arc, airborne knees flexed",
                "idle": "subtle breathing stance, resting ready pose, relaxed arms",
                "attack": "weapon strike action, kinetic attack slash",
                "talk": "expressive facial expression, dialogue pose"
            }
            extra = action_tags.get(action.lower(), f"{action} pose")
            
            # Anti-multi-character & anti-spritesheet protection
            anti_sheet_pos = "single character, solo"
            if perspective == "portrait":
                anti_sheet_pos += ", centered bust shot, head and shoulders portrait"
            
            context["positive_prompt"] = f"{anti_sheet_pos}, {pos}, {extra}, consistent character design, matching clothing and colors"

            neg = context.get("negative_prompt", "")
            sheet_neg = (
                "multiple characters, multiple views, character sheet, expressions sheet, "
                "portrait sheet, collage, montage, side by side, extra heads, duplicate heads, "
                "cloned face, border avatars, icons, split view, multi-panel, comic layout"
            )
            if perspective == "portrait":
                sheet_neg += ", full body, feet, shoes, legs, standing full length"
                
            context["negative_prompt"] = f"{sheet_neg}, {neg}".strip(", ")

        return context
