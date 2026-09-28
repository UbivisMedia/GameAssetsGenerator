"""
ComfyUI Client
Manages communication with the ComfyUI API via REST and WebSocket.
Handles queueing, progress tracking, and retrieval of generated image outputs.
"""

import json
import logging
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("ComfyClient")


class ComfyClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188", timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())

    def check_connection(self) -> Dict[str, Any]:
        """Checks if ComfyUI is reachable and returns basic system info."""
        try:
            req = urllib.request.Request(f"{self.base_url}/system_stats")
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return {
                        "online": True,
                        "url": self.base_url,
                        "system": data.get("system", {}),
                        "devices": data.get("devices", [])
                    }
        except Exception as e:
            logger.warning(f"ComfyUI connection check failed: {e}")
            return {
                "online": False,
                "url": self.base_url,
                "error": str(e)
            }
        return {"online": False, "url": self.base_url, "error": "Unknown status"}

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Fetches history for a given prompt_id."""
        try:
            url = f"{self.base_url}/history/{prompt_id}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Error fetching history for {prompt_id}: {e}")
        return {}

    def get_image_data(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Downloads image bytes from ComfyUI /view endpoint."""
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        url = f"{self.base_url}/view?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()

    def queue_prompt(self, workflow_prompt: Dict[str, Any]) -> Optional[str]:
        """Submits a prompt graph to ComfyUI /prompt and returns the prompt_id."""
        payload = {
            "prompt": workflow_prompt,
            "client_id": self.client_id
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/prompt",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("prompt_id")
        except Exception as e:
            logger.error(f"Failed to queue prompt to ComfyUI: {e}")
            raise RuntimeError(f"ComfyUI queue prompt error: {e}")

    def inject_parameters(
        self,
        workflow: Dict[str, Any],
        positive_prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        seed: Optional[int] = None,
        steps: int = 25,
        cfg: float = 7.5,
        batch_size: int = 1
    ) -> Dict[str, Any]:
        """
        Dynamically finds and configures nodes in standard ComfyUI API workflows:
        - CLIPTextEncode (Positive / Negative)
        - EmptyLatentImage (Width, Height, Batch Size)
        - KSampler (Seed, Steps, CFG)
        """
        import copy
        wf = copy.deepcopy(workflow)

        # Identify positive and negative nodes by checking connections to KSampler
        ksampler_nodes = [k for k, v in wf.items() if v.get("class_type") in ("KSampler", "KSamplerAdvanced")]
        pos_id, neg_id = None, None

        if ksampler_nodes:
            ks_inputs = wf[ksampler_nodes[0]].get("inputs", {})
            pos_link = ks_inputs.get("positive")
            neg_link = ks_inputs.get("negative")
            if isinstance(pos_link, list) and len(pos_link) > 0:
                pos_id = str(pos_link[0])
            if isinstance(neg_link, list) and len(neg_link) > 0:
                neg_id = str(neg_link[0])

        for node_id, node in wf.items():
            class_type = node.get("class_type", "")
            inputs = node.setdefault("inputs", {})

            # KSampler parameters
            if class_type in ("KSampler", "KSamplerAdvanced"):
                if seed is not None:
                    inputs["seed"] = seed
                if steps:
                    inputs["steps"] = steps
                if cfg:
                    inputs["cfg"] = cfg

            # Dimensions
            elif class_type in ("EmptyLatentImage", "EmptySD3LatentImage", "EmptyFluxLatent"):
                inputs["width"] = width
                inputs["height"] = height
                if "batch_size" in inputs:
                    inputs["batch_size"] = batch_size

            # Prompts
            elif class_type == "CLIPTextEncode":
                if pos_id and node_id == pos_id:
                    inputs["text"] = positive_prompt
                elif neg_id and node_id == neg_id:
                    inputs["text"] = negative_prompt
                else:
                    # Heuristic fallback based on title / content
                    title = node.get("_meta", {}).get("title", "").lower()
                    if "negative" in title:
                        inputs["text"] = negative_prompt
                    elif "positive" in title or not pos_id:
                        inputs["text"] = positive_prompt
                        pos_id = node_id

        return wf

    def wait_for_completion(
        self,
        prompt_id: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> List[Tuple[str, str, str]]:
        """
        Polls ComfyUI history until prompt is finished or timeout occurs.
        Returns list of (filename, subfolder, type) tuples.
        """
        start_time = time.time()
        poll_interval = 0.5

        while time.time() - start_time < self.timeout:
            history = self.get_history(prompt_id)
            if prompt_id in history:
                prompt_output = history[prompt_id]
                outputs = prompt_output.get("outputs", {})
                images_info = []

                for _, node_output in outputs.items():
                    if "images" in node_output:
                        for img in node_output["images"]:
                            images_info.append((
                                img.get("filename", ""),
                                img.get("subfolder", ""),
                                img.get("type", "output")
                            ))

                if images_info:
                    return images_info

                # If outputs has no images, check status
                status = prompt_output.get("status", {})
                if status.get("completed", False):
                    return images_info
                if status.get("status_str") == "error":
                    raise RuntimeError(f"ComfyUI prompt execution failed: {status.get('messages')}")

            if progress_callback:
                progress_callback({
                    "prompt_id": prompt_id,
                    "elapsed": round(time.time() - start_time, 1),
                    "status": "processing"
                })

            time.sleep(poll_interval)

        raise TimeoutError(f"ComfyUI timed out after {self.timeout}s waiting for {prompt_id}")
