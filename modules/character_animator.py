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
            
            # Anti-multi-character, anti-stacking & anti-spritesheet protection
            anti_sheet_pos = "single character, solo"
            if perspective == "portrait":
                # Only frame as bust if prompt does NOT explicitly specify full-body clothing/shoes
                has_lower_body = any(t in pos.lower() for t in ["shoes", "schuhe", "hose", "pants", "jeans", "feet", "legs", "stöckelschuhe", "boots", "full body"])
                if not has_lower_body:
                    anti_sheet_pos += ", centered bust shot, head and shoulders portrait"
                else:
                    anti_sheet_pos += ", centered composition, single person"
            elif perspective == "full_body":
                anti_sheet_pos += ", standing full body shot, visible head to toe, complete standing silhouette"
            
            context["positive_prompt"] = f"{anti_sheet_pos}, {pos}, {extra}, consistent character design, matching clothing and colors"

            neg = context.get("negative_prompt", "")
            sheet_neg = (
                "stacked, vertically stacked, stacked heads, double head, two heads, multiple heads, "
                "cloned head, extra face, double bust, two bodies, split image, horizontal split, two people, twin, "
                "multiple characters, multiple views, character sheet, expressions sheet, "
                "portrait sheet, collage, montage, side by side, border avatars, icons, split view, multi-panel, comic layout"
            )
            if perspective == "portrait":
                has_lower_body = any(t in pos.lower() for t in ["shoes", "schuhe", "hose", "pants", "jeans", "feet", "legs", "stöckelschuhe", "boots", "full body"])
                if not has_lower_body:
                    sheet_neg += ", full body, feet, shoes, legs, standing full length"
                
            context["negative_prompt"] = f"{sheet_neg}, {neg}".strip(", ")

        return context
