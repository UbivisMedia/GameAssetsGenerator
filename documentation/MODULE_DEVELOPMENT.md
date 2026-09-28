# Module Development Guide (Plugin Interface)

The **GameAssetGenerator** features a dynamic module and plugin system. Any Python script or package located in the `modules/` directory that inherits from `BaseAssetModule` will be automatically detected, loaded, and hooked into the generation lifecycle at application startup.

---

## 1. The `BaseAssetModule` Interface

All modules inherit from `lib.module_interface.BaseAssetModule`:

```python
from typing import Any, Dict, List
from PIL import Image
from lib.module_interface import BaseAssetModule

class MyCustomModule(BaseAssetModule):
    # Unique identifier and metadata
    module_id: str = "my_custom_module"
    name: str = "My Custom Module"
    version: str = "1.0.0"
    description: str = "Extends the generator with custom logic."
    author: str = "Your Name"
    enabled: bool = True

    def on_register(self, manager: Any) -> None:
        """Called immediately after the module is discovered and loaded."""
        pass

    def on_prompt_prepare(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook executed before prompts are dispatched to ComfyUI or LM Studio.
        Can inspect and modify:
        - context['positive_prompt']
        - context['negative_prompt']
        - context['category']
        - context['action']
        """
        return context

    def on_workflow_prepare(self, workflow: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook executed before the ComfyUI workflow JSON is queued.
        Allows injecting custom nodes (e.g. LoRA loaders, ControlNet, Rembg).
        """
        return workflow

    def on_postprocess(self, frames: List[Image.Image], context: Dict[str, Any]) -> List[Image.Image]:
        """
        Hook executed after image generation and slicing, before saving.
        Enables custom shaders, color palette quantization, outline generation, etc.
        Must return a list of PIL Image objects.
        """
        return frames

    def register_routes(self, app: Any) -> None:
        """
        Hook to register custom FastAPI endpoints on the backend server.
        """
        pass
```

---

## 2. Practical Example: Palette Quantization Shader

Create a file `modules/gameboy_filter.py`:

```python
from typing import Any, Dict, List
from PIL import Image
from lib.module_interface import BaseAssetModule

class GameBoyFilterModule(BaseAssetModule):
    module_id = "gameboy_filter"
    name = "Game Boy Palette Filter"
    version = "1.0.0"
    description = "Restricts all generated frames to the authentic 4-color Game Boy palette."
    author = "GameDev"
    enabled = True

    GB_PALETTE = [
        (15, 56, 15),     # Darkest green
        (48, 98, 48),     # Dark green
        (139, 172, 15),   # Light green
        (155, 188, 15)    # Lightest green
    ]

    def on_postprocess(self, frames: List[Image.Image], context: Dict[str, Any]) -> List[Image.Image]:
        pal_img = Image.new("P", (1, 1))
        flat = []
        for rgb in self.GB_PALETTE:
            flat.extend(rgb)
        while len(flat) < 768:
            flat.extend((0, 0, 0))
        pal_img.putpalette(flat)

        processed = []
        for frame in frames:
            alpha = frame.split()[-1]
            quantized = frame.convert("RGB").quantize(palette=pal_img).convert("RGBA")
            quantized.putalpha(alpha)
            processed.append(quantized)

        return processed
```

Once dropped into `modules/`, it is automatically detected and integrated!

---

## 3. Bundled Starter Modules

Reference implementations are available in `modules/`:
1. `modules/character_animator.py`: Pose consistency and silhouette preservation for characters.
2. `modules/item_generator.py`: Optimized framing for inventory icons and collectible props.
3. `modules/palette_quantizer.py`: Retro palette reduction for Pico-8 and Game Boy aesthetics with dithering.
