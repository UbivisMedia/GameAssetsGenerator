"""
LM Studio Client
Connects to local LM Studio via OpenAI-compatible API (/v1/chat/completions).
Handles prompt refinement, perspective adherence, and multi-step animation keyframe planning.
"""

import json
import logging
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("LMClient")


class LMClient:
    def __init__(self, base_url: str = "http://127.0.0.1:1234/v1", model: str = "local-model", temperature: float = 0.7):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature

    def check_connection(self) -> Dict[str, Any]:
        """Checks if LM Studio local server is online."""
        try:
            req = urllib.request.Request(f"{self.base_url}/models")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("id") for m in data.get("data", [])]
                    return {
                        "online": True,
                        "url": self.base_url,
                        "models": models,
                        "selected_model": self.model
                    }
        except Exception as e:
            return {
                "online": False,
                "url": self.base_url,
                "error": str(e)
            }
        return {"online": False, "url": self.base_url, "error": "Unknown status"}

    def complete_chat(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
        """Sends a chat completion request to LM Studio."""
        temp = temperature if temperature is not None else self.temperature
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temp,
            "stream": False
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            choices = res.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()
        return ""

    def enhance_asset_prompt(
        self,
        user_prompt: str,
        category: str,
        perspective_data: Dict[str, Any],
        style_prompt: str
    ) -> Dict[str, Any]:
        """
        Generates enriched positive & negative prompts tailored for game assets.
        Falls back to rule-based generation if LM Studio is not accessible.
        """
        persp_prefix = perspective_data.get("prompt_prefix", "")
        persp_neg = perspective_data.get("negative_prompt", "")
        persp_name = perspective_data.get("name", "Standard")

        system_instruction = (
            "You are an expert Game Asset Technical Artist. Convert the user's asset idea into "
            "concise, highly effective prompts for Stable Diffusion. Output valid JSON ONLY with keys: "
            "'positive_prompt', 'negative_prompt', 'tags'."
        )

        user_content = (
            f"Asset Concept: {user_prompt}\n"
            f"Category: {category}\n"
            f"Perspective: {persp_name} ({persp_prefix})\n"
            f"Style: {style_prompt}\n"
            f"Requirements: Single isolated asset on pure plain white background, full body view, sharp silhouette."
        )

        try:
            raw_text = self.complete_chat(system_instruction, user_content)
            # Try parsing JSON from LLM response
            start_idx = raw_text.find("{")
            end_idx = raw_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                json_str = raw_text[start_idx : end_idx + 1]
                data = json.loads(json_str)
                pos = data.get("positive_prompt", "")
                neg = data.get("negative_prompt", "")
                # Ensure essential perspective & style tokens are present
                if persp_prefix.lower() not in pos.lower():
                    pos = f"{persp_prefix}, {pos}"
                if style_prompt.lower() not in pos.lower():
                    pos = f"{pos}, {style_prompt}"
                return {
                    "positive_prompt": pos,
                    "negative_prompt": f"{persp_neg}, {neg}".strip(", "),
                    "source": "lm_studio",
                    "tags": data.get("tags", [])
                }
        except Exception as e:
            logger.info(f"LM Studio unavailable or error ({e}), using rule-based synthesis.")

        # Offline fallback synthesis
        positive = (
            f"{persp_prefix}, {style_prompt}, game asset of {user_prompt}, "
            f"isolated sprite on clean plain white background, crisp silhouette, centered composition"
        )
        negative = (
            f"{persp_neg}, blurry, low quality, photorealistic, noise, 3d render distortion, "
            f"cropped, cut off, complex background, watermark, text"
        )
        return {
            "positive_prompt": positive,
            "negative_prompt": negative,
            "source": "rule_based_fallback",
            "tags": [category, perspective_data.get("id", "")]
        }

    def plan_animation_steps(
        self,
        asset_name: str,
        action: str,
        steps_count: int,
        perspective_data: Dict[str, Any],
        step_templates: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Creates detailed frame-by-frame instructions for the animation steps (e.g. walk, sit, jump).
        """
        persp_prefix = perspective_data.get("prompt_prefix", "")

        # Try LM Studio first if available
        system_instruction = (
            "You are a 2D game animator. Generate frame-by-frame pose descriptions for a sprite animation. "
            "Output JSON ONLY as an array of objects with keys: 'step', 'pose_title', 'prompt_extension'."
        )
        user_content = (
            f"Character/Asset: {asset_name}\n"
            f"Action: {action}\n"
            f"Frames/Steps: {steps_count}\n"
            f"Perspective: {perspective_data.get('name', '')} ({persp_prefix})\n"
            f"Ensure consecutive frames create smooth movement and preserve character proportions."
        )

        try:
            raw_text = self.complete_chat(system_instruction, user_content)
            start_idx = raw_text.find("[")
            end_idx = raw_text.rfind("]")
            if start_idx != -1 and end_idx != -1:
                frames = json.loads(raw_text[start_idx : end_idx + 1])
                if len(frames) == steps_count:
                    return frames
        except Exception:
            pass

        # Offline / fallback heuristic step generation
        results = []
        templates = step_templates or []
        for i in range(steps_count):
            step_num = i + 1
            desc = templates[i] if i < len(templates) else f"Phase {step_num} of {steps_count} for {action}"
            results.append({
                "step": step_num,
                "pose_title": desc,
                "prompt_extension": f"frame {step_num} of {steps_count} animation sequence, {action} action: {desc}"
            })
        return results
