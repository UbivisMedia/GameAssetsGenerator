"""
Configuration Manager
Loads, caches, and updates settings files from the settings/ directory.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigManager:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.settings_dir = self.base_dir / "settings"
        self._cache: Dict[str, Any] = {}
        self.reload_all()

    def reload_all(self):
        """Reloads all JSON configuration files from settings/."""
        self._cache["config"] = self._load_json("config.json", default={})
        self._cache["categories"] = self._load_json("categories.json", default={"categories": []})
        self._cache["perspectives"] = self._load_json("perspectives.json", default={"perspectives": []})
        self._cache["resolutions"] = self._load_json("resolutions.json", default={"presets": [], "scaling_modes": []})
        self._cache["animations"] = self._load_json("animations.json", default={"actions": []})
        self._cache["model_presets"] = self._load_json("model_presets.json", default={"families": []})

    def _load_json(self, filename: str, default: Any = None) -> Any:
        path = self.settings_dir / filename
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ConfigManager] Error reading {filename}: {e}")
            return default

    def save_json(self, filename: str, data: Any) -> bool:
        path = self.settings_dir / filename
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            cache_key = Path(filename).stem
            self._cache[cache_key] = data
            return True
        except Exception as e:
            print(f"[ConfigManager] Error saving {filename}: {e}")
            return False

    @property
    def config(self) -> Dict[str, Any]:
        return self._cache.get("config", {})

    @property
    def categories(self) -> List[Dict[str, Any]]:
        return self._cache.get("categories", {}).get("categories", [])

    @property
    def perspectives(self) -> List[Dict[str, Any]]:
        return self._cache.get("perspectives", {}).get("perspectives", [])

    @property
    def resolutions(self) -> Dict[str, Any]:
        return self._cache.get("resolutions", {})

    @property
    def animations(self) -> List[Dict[str, Any]]:
        return self._cache.get("animations", {}).get("actions", [])

    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        for cat in self.categories:
            if cat.get("id") == category_id:
                return cat
        return None

    def get_perspective(self, perspective_id: str) -> Optional[Dict[str, Any]]:
        for p in self.perspectives:
            if p.get("id") == perspective_id:
                return p
        return None

    def get_animation_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        for a in self.animations:
            if a.get("id") == action_id:
                return a
        return None

    def get_resolution_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        for r in self.resolutions.get("presets", []):
            if r.get("id") == preset_id:
                return r
        return None

    @property
    def model_presets(self) -> List[Dict[str, Any]]:
        return self._cache.get("model_presets", {}).get("families", [])

    def get_model_preset(self, model_name: Optional[str]) -> Dict[str, Any]:
        """Finds matching model architecture preset based on filename patterns."""
        if not model_name:
            fallback = next((f for f in self.model_presets if "*" in f.get("match_patterns", [])), None)
            return fallback or (self.model_presets[0] if self.model_presets else {})

        name_lower = model_name.lower().replace("\\", "/")
        # 1. Exact or substring match (excluding wildcard)
        for fam in self.model_presets:
            for pat in fam.get("match_patterns", []):
                if pat != "*" and pat in name_lower:
                    return fam

        # 2. Wildcard fallback
        for fam in self.model_presets:
            if "*" in fam.get("match_patterns", []):
                return fam

        return self.model_presets[0] if self.model_presets else {}

