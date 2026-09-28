"""
Module Manager
Discovers, loads, and manages lifecycle execution of plugins in the modules/ directory.
"""

import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

from .module_interface import BaseAssetModule

logger = logging.getLogger("ModuleManager")


class ModuleManager:
    def __init__(self, modules_dir: Optional[Path] = None):
        self.modules_dir = modules_dir or (Path(__file__).resolve().parent.parent / "modules")
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        self.modules: Dict[str, BaseAssetModule] = {}

    def discover_and_load_modules(self) -> Dict[str, BaseAssetModule]:
        """Scans the modules directory and loads all valid BaseAssetModule subclasses."""
        self.modules.clear()
        if not self.modules_dir.exists():
            return self.modules

        for path in self.modules_dir.glob("*.py"):
            if path.name.startswith("__") or path.name.startswith("."):
                continue
            self._load_module_file(path)

        for sub_dir in self.modules_dir.iterdir():
            if sub_dir.is_dir() and not sub_dir.name.startswith("__") and not sub_dir.name.startswith("."):
                init_file = sub_dir / "__init__.py"
                if init_file.exists():
                    self._load_module_file(init_file, module_name=sub_dir.name)

        logger.debug(f"Loaded {len(self.modules)} active modules: {list(self.modules.keys())}")
        return self.modules

    def _load_module_file(self, file_path: Path, module_name: Optional[str] = None):
        mod_name = module_name or file_path.stem
        try:
            spec = importlib.util.spec_from_file_location(f"modules.{mod_name}", file_path)
            if spec and spec.loader:
                py_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(py_mod)

                # Look for BaseAssetModule subclasses
                for attr_name in dir(py_mod):
                    attr = getattr(py_mod, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, BaseAssetModule)
                        and attr is not BaseAssetModule
                    ):
                        instance = attr()
                        instance.on_register(self)
                        mod_id = getattr(instance, "module_id", mod_name)
                        self.modules[mod_id] = instance
                        logger.debug(f"Successfully registered module: {mod_id} ({instance.name})")
        except Exception as e:
            logger.error(f"Failed to load module from {file_path}: {e}")

    def list_modules(self) -> List[Dict[str, Any]]:
        """Returns metadata for all loaded modules."""
        return [m.get_info() for m in self.modules.values()]

    def run_prompt_prepare(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the prompt prepare hook across all enabled modules."""
        ctx = dict(context)
        for mod in self.modules.values():
            if mod.enabled:
                try:
                    ctx = mod.on_prompt_prepare(ctx)
                except Exception as e:
                    logger.error(f"Module {mod.module_id} failed in on_prompt_prepare: {e}")
        return ctx

    def run_workflow_prepare(self, workflow: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the workflow prepare hook across all enabled modules."""
        wf = dict(workflow)
        for mod in self.modules.values():
            if mod.enabled:
                try:
                    wf = mod.on_workflow_prepare(wf, context)
                except Exception as e:
                    logger.error(f"Module {mod.module_id} failed in on_workflow_prepare: {e}")
        return wf

    def run_postprocess(self, frames: List[Image.Image], context: Dict[str, Any]) -> List[Image.Image]:
        """Runs postprocessing image modifications across all enabled modules."""
        res_frames = list(frames)
        for mod in self.modules.values():
            if mod.enabled:
                try:
                    res_frames = mod.on_postprocess(res_frames, context)
                except Exception as e:
                    logger.error(f"Module {mod.module_id} failed in on_postprocess: {e}")
        return res_frames

    def register_routes(self, app: Any) -> None:
        """Invokes register_routes on all loaded modules."""
        for mod in self.modules.values():
            if mod.enabled:
                try:
                    mod.register_routes(app)
                except Exception as e:
                    logger.error(f"Module {mod.module_id} failed to register routes: {e}")
