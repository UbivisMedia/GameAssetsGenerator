"""
Item & Prop Generator Module
Specializes prompts for inventory items, weapons, potions, and equipment icons.
"""

from typing import Any, Dict
from lib.module_interface import BaseAssetModule


class ItemGeneratorModule(BaseAssetModule):
    module_id = "item_generator"
    name = "Item & Equipment Optimizer"
    version = "1.0.0"
    description = "Optimizes icons and props for inventories and collectibles with high readability."
    author = "GameAssetGenerator Core"
    enabled = True

    def on_prompt_prepare(self, context: Dict[str, Any]) -> Dict[str, Any]:
        category = context.get("category", "")
        if category in ("items", "props"):
            pos = context.get("positive_prompt", "")
            context["positive_prompt"] = (
                f"{pos}, inventory icon framing, centered object, high readability, "
                f"clear lighting highlight, sharp outline, iconic game silhouette"
            )
            neg = context.get("negative_prompt", "")
            context["negative_prompt"] = f"{neg}, character holding item, human hands, room background, cropped edges"
        return context
