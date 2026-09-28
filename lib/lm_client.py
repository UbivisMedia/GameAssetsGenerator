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
    def __init__(self, base_url: str = "http://127.0.0.1:1234/v1", model: Optional[str] = None, temperature: float = 0.7):
        self.base_url = base_url.rstrip("/")
        # Root url without /v1
        self.root_url = self.base_url[:-3] if self.base_url.endswith("/v1") else self.base_url
        self.model = model or "local-model"
        self.temperature = temperature

    def check_connection(self) -> Dict[str, Any]:
        """Checks if LM Studio is reachable and detects loaded/available models."""
        try:
            # Query /api/v0/models for rich status if available
            loaded_model = None
            models_list = []
            
            try:
                req_v0 = urllib.request.Request(f"{self.root_url}/api/v0/models")
                with urllib.request.urlopen(req_v0, timeout=3) as resp_v0:
                    data_v0 = json.loads(resp_v0.read().decode("utf-8"))
                    for m in data_v0.get("data", []):
                        m_id = m.get("id")
                        models_list.append(m_id)
                        if m.get("state") == "loaded":
                            loaded_model = m_id
            except Exception:
                pass

            if not models_list:
                # Fallback to OpenAI standard /v1/models
                req = urllib.request.Request(f"{self.base_url}/models")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        models_list = [m.get("id") for m in data.get("data", [])]

            if loaded_model:
                self.model = loaded_model

            has_loaded = bool(loaded_model)
            return {
                "online": True,
                "url": self.base_url,
                "models": models_list,
                "loaded_model": loaded_model,
                "has_loaded_model": has_loaded,
                "selected_model": self.model if has_loaded else "None (Model not loaded)"
            }
        except Exception as e:
            return {
                "online": False,
                "url": self.base_url,
                "error": str(e),
                "has_loaded_model": False
            }

    def get_models(self) -> List[Dict[str, Any]]:
        """Returns details of all installed models in LM Studio."""
        results = []
        try:
            req = urllib.request.Request(f"{self.root_url}/api/v0/models")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for m in data.get("data", []):
                    results.append({
                        "id": m.get("id"),
                        "name": m.get("id"),
                        "type": m.get("type", "llm"),
                        "state": m.get("state", "not-loaded"),
                        "is_loaded": m.get("state") == "loaded",
                        "size": m.get("quantization", "")
                    })
        except Exception:
            # Fallback to /v1/models
            try:
                req = urllib.request.Request(f"{self.base_url}/models")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for m in data.get("data", []):
                        m_id = m.get("id")
                        results.append({
                            "id": m_id,
                            "name": m_id,
                            "type": "llm",
                            "state": "unknown",
                            "is_loaded": True
                        })
            except Exception:
                pass
        return results

    def load_model(self, model_id: str) -> Dict[str, Any]:
        """Loads a model into LM Studio using lms CLI or API."""
        import subprocess
        try:
            cmd = ["lms", "load", model_id, "-y", "--gpu", "max"]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if p.returncode == 0:
                self.model = model_id
                return {"status": "success", "model": model_id, "output": p.stdout}
            return {"status": "error", "message": p.stderr or p.stdout}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def complete_chat(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
        """Sends a chat completion request to LM Studio."""
        temp = temperature if temperature is not None else self.temperature

        # Ensure we have the active loaded model
        if self.model in ("local-model", None, ""):
            conn = self.check_connection()
            if conn.get("loaded_model"):
                self.model = conn["loaded_model"]
            elif conn.get("models"):
                # Filter out embedding models
                llm_candidates = [m for m in conn["models"] if "embed" not in m.lower()]
                if llm_candidates:
                    self.load_model(llm_candidates[0])

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
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                choices = res.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "").strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.error(f"LM Studio chat completion HTTP error {e.code}: {err_body}")
            raise RuntimeError(f"LM Studio Error: {err_body}")
        except Exception as e:
            logger.error(f"LM Studio chat completion error: {e}")
            raise
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
