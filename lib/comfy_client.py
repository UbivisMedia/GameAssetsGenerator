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

    def get_available_models(self) -> Dict[str, Any]:
        """
        Queries ComfyUI object_info to retrieve all installed checkpoints,
        unets, loras, vaes, and sampler options.
        """
        models = {
            "checkpoints": [],
            "unets": [],
            "loras": [],
            "vaes": [],
            "samplers": [],
            "schedulers": []
        }
        try:
            url = f"{self.base_url}/object_info"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if "CheckpointLoaderSimple" in data:
                models["checkpoints"] = data["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
            if "UNETLoader" in data:
                models["unets"] = data["UNETLoader"]["input"]["required"]["unet_name"][0]
            if "LoraLoader" in data:
                models["loras"] = data["LoraLoader"]["input"]["required"]["lora_name"][0]
            if "VAELoader" in data:
                models["vaes"] = data["VAELoader"]["input"]["required"]["vae_name"][0]
            if "KSampler" in data:
                models["samplers"] = data["KSampler"]["input"]["required"]["sampler_name"][0]
                models["schedulers"] = data["KSampler"]["input"]["required"]["scheduler"][0]
        except Exception as e:
            logger.warning(f"Failed to fetch ComfyUI models: {e}")
        return models

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
        batch_size: int = 1,
        checkpoint: Optional[str] = None,
        unet: Optional[str] = None,
        lora: Optional[str] = None,
        lora_strength: float = 1.0,
        vae: Optional[str] = None,
        sampler_name: Optional[str] = None,
        scheduler: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically finds and configures nodes in standard ComfyUI API workflows:
        - CheckpointLoaderSimple (Dynamic Checkpoint selection with auto-fallback)
        - LoraLoader (Dynamically injected if specified)
        - VAELoader (Optional external VAE)
        - CLIPTextEncode (Positive / Negative)
        - EmptyLatentImage (Width, Height, Batch Size)
        - KSampler (Seed, Steps, CFG, Sampler, Scheduler)
        """
        import copy
        wf = copy.deepcopy(workflow)

        # 1. Resolve Checkpoint
        available = self.get_available_models()
        avail_ckpts = available.get("checkpoints", [])

        # Find CheckpointLoaderSimple node
        ckpt_nodes = [k for k, v in wf.items() if v.get("class_type") in ("CheckpointLoaderSimple", "CheckpointLoader")]
        ckpt_node_id = ckpt_nodes[0] if ckpt_nodes else None

        if ckpt_node_id:
            current_ckpt = wf[ckpt_node_id].get("inputs", {}).get("ckpt_name", "")
            target_ckpt = checkpoint

            # If user didn't specify checkpoint or specified one not in ComfyUI, auto-fallback
            if not target_ckpt or (avail_ckpts and target_ckpt not in avail_ckpts):
                if avail_ckpts:
                    # Filter out non-image models (audio, music, etc.)
                    image_ckpts = [
                        c for c in avail_ckpts
                        if not any(skip in c.lower() for skip in ("audio", "yue", "music", "sound", "voice"))
                    ]
                    candidates = image_ckpts or avail_ckpts
                    # Prefer standard SD1.5 or anime/pixel art checkpoints
                    pref = [c for c in candidates if "sd 1.5" in c.lower() or "anime" in c.lower()]
                    target_ckpt = pref[0] if pref else candidates[0]
                else:
                    target_ckpt = current_ckpt

            if target_ckpt:
                wf[ckpt_node_id]["inputs"]["ckpt_name"] = target_ckpt
                logger.info(f"Using ComfyUI Checkpoint: {target_ckpt}")

        # 2. Inject or Configure LoRA if requested
        if lora and lora.strip() and lora.lower() != "none" and ckpt_node_id:
            existing_loras = [k for k, v in wf.items() if v.get("class_type") == "LoraLoader"]
            if existing_loras:
                wf[existing_loras[0]]["inputs"]["lora_name"] = lora
                wf[existing_loras[0]]["inputs"]["strength_model"] = lora_strength
                wf[existing_loras[0]]["inputs"]["strength_clip"] = lora_strength
            else:
                numeric_ids = [int(k) for k in wf.keys() if k.isdigit()]
                lora_id = str(max(numeric_ids, default=100) + 1)
                wf[lora_id] = {
                    "class_type": "LoraLoader",
                    "inputs": {
                        "lora_name": lora,
                        "strength_model": lora_strength,
                        "strength_clip": lora_strength,
                        "model": [ckpt_node_id, 0],
                        "clip": [ckpt_node_id, 1]
                    },
                    "_meta": {"title": f"Load LoRA ({lora})"}
                }
                # Rewire nodes that connected to ckpt model/clip to lora
                for nid, n in wf.items():
                    if nid in (lora_id, ckpt_node_id):
                        continue
                    for in_name, in_val in n.get("inputs", {}).items():
                        if isinstance(in_val, list) and len(in_val) >= 2:
                            if str(in_val[0]) == ckpt_node_id and in_val[1] == 0:
                                n["inputs"][in_name] = [lora_id, 0]
                            elif str(in_val[0]) == ckpt_node_id and in_val[1] == 1:
                                n["inputs"][in_name] = [lora_id, 1]
                logger.info(f"Injected LoRA: {lora} (strength: {lora_strength})")

        # 3. Inject or Configure Custom VAE if requested
        if vae and vae.strip() and vae.lower() != "default":
            existing_vaes = [k for k, v in wf.items() if v.get("class_type") == "VAELoader"]
            if existing_vaes:
                wf[existing_vaes[0]]["inputs"]["vae_name"] = vae
            else:
                numeric_ids = [int(k) for k in wf.keys() if k.isdigit()]
                vae_id = str(max(numeric_ids, default=200) + 2)
                wf[vae_id] = {
                    "class_type": "VAELoader",
                    "inputs": {"vae_name": vae},
                    "_meta": {"title": f"Load VAE ({vae})"}
                }
                for nid, n in wf.items():
                    if n.get("class_type") == "VAEDecode":
                        n.setdefault("inputs", {})["vae"] = [vae_id, 0]
                logger.info(f"Using Custom VAE: {vae}")

        # 4. Identify positive and negative nodes by checking connections to KSampler
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
                if sampler_name:
                    inputs["sampler_name"] = sampler_name
                if scheduler:
                    inputs["scheduler"] = scheduler

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
