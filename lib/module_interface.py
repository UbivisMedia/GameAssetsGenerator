"""
Module Interface
Defines the base class and hook contracts that all custom modules in modules/ must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from PIL import Image


class BaseAssetModule(ABC):
    """
    Base class for GameAssetGenerator modules.
    Inherit from this class and place your module in the modules/ directory.
    """

    # Module Metadata
    module_id: str = "base_module"
    name: str = "Base Asset Module"
    version: str = "1.0.0"
    description: str = "Base class for generator extensions."
    author: str = "Community"
    enabled: bool = True

    def __init__(self):
        pass

    def on_register(self, manager: Any) -> None:
        """Called when the module is loaded and registered into the system."""
        pass

    def on_prompt_prepare(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook called right before prompts are sent to ComfyUI or LM Studio.
        Can modify context['positive_prompt'], context['negative_prompt'], etc.
        Must return the updated or unmodified context dict.
        """
        return context

    def on_workflow_prepare(self, workflow: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook called before the ComfyUI workflow JSON is queued.
        Can inject custom nodes (e.g. LoRA loaders, ControlNet, Rembg).
        Must return the updated workflow dict.
        """
        return workflow

    def on_postprocess(self, frames: List[Image.Image], context: Dict[str, Any]) -> List[Image.Image]:
        """
        Hook called after images are generated and sliced, before saving.
        Can perform pixel-art effects (palette quantization, outline enhancement, dithering).
        Must return the processed list of PIL Image objects.
        """
        return frames

    def register_routes(self, app: Any) -> None:
        """
        Hook to attach custom REST API endpoints to the web server.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Returns summary info about the module."""
        return {
            "id": self.module_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled
        }
