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

    def upload_image(self, image_bytes: bytes, filename: str = "gag_ref.png") -> str:
        """
        Uploads an image to ComfyUI (/upload/image) for use in LoadImage nodes.
        Returns the filename assigned by ComfyUI.
        """
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        body = []
        body.append(f"--{boundary}\r\n".encode())
        body.append(f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode())
        body.append(b"Content-Type: image/png\r\n\r\n")
        body.append(image_bytes)
        body.append(b"\r\n")
        body.append(f"--{boundary}\r\n".encode())
        body.append(b'Content-Disposition: form-data; name="overwrite"\r\n\r\n')
        body.append(b"true\r\n")
        body.append(f"--{boundary}--\r\n".encode())
        payload = b"".join(body)

        req = urllib.request.Request(
            f"{self.base_url}/upload/image",
            data=payload,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("name", filename)
        except Exception as e:
            logger.error(f"Failed to upload reference image to ComfyUI: {e}")
            raise

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
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            logger.error(f"Failed to queue prompt to ComfyUI: {e} - Response: {err_body}")
            raise RuntimeError(f"ComfyUI queue prompt error: {e}. Details: {err_body}")
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
            "clips": [],
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
            if "CLIPLoader" in data:
                models["clips"] = data["CLIPLoader"]["input"]["required"]["clip_name"][0]
            if "KSampler" in data:
                models["samplers"] = data["KSampler"]["input"]["required"]["sampler_name"][0]
                models["schedulers"] = data["KSampler"]["input"]["required"]["scheduler"][0]
        except Exception as e:
            logger.warning(f"Failed to fetch ComfyUI models: {e}")
        return models

    @staticmethod
    def _resolve_model_name(requested_name: Optional[str], available_list: List[str]) -> Optional[str]:
        if not requested_name or not available_list:
            return requested_name
        if requested_name in available_list:
            return requested_name
        norm_back = requested_name.replace("/", "\\")
        if norm_back in available_list:
            return norm_back
        norm_fwd = requested_name.replace("\\", "/")
        if norm_fwd in available_list:
            return norm_fwd
        req_lower = requested_name.lower()
        norm_back_lower = norm_back.lower()
        for item in available_list:
            if item.lower() in (req_lower, norm_back_lower):
                return item
        from pathlib import Path
        req_base = Path(requested_name).name.lower()
        for item in available_list:
            if Path(item).name.lower() == req_base:
                return item
        return requested_name

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
        scheduler: Optional[str] = None,
        reference_image: Optional[str] = None,
        denoise: float = 1.0,
        model_preset: Optional[Dict[str, Any]] = None,
        remove_background: bool = False
    ) -> Dict[str, Any]:
        """
        Dynamically finds and configures nodes in standard ComfyUI API workflows:
        - CheckpointLoaderSimple (Dynamic Checkpoint selection with auto-fallback)
        - LoraLoader (Dynamically injected if specified)
        - VAELoader (Optional external VAE)
        - CLIPTextEncode (Positive / Negative)
        - EmptyLatentImage (Width, Height, Batch Size)
        - LoadImage + VAEEncode (Reference Image chaining for frame-by-frame animation)
        - KSampler (Seed, Steps, CFG, Sampler, Scheduler, Denoise)
        """
        import copy
        wf = copy.deepcopy(workflow)

        # 1. Resolve Checkpoint
        available = self.get_available_models()
        avail_ckpts = available.get("checkpoints", [])
        avail_unets = available.get("unets", [])
        avail_loras = available.get("loras", [])
        avail_vaes = available.get("vaes", [])

        # Find CheckpointLoaderSimple node
        ckpt_nodes = [k for k, v in wf.items() if v.get("class_type") in ("CheckpointLoaderSimple", "CheckpointLoader")]
        ckpt_node_id = ckpt_nodes[0] if ckpt_nodes else None

        if ckpt_node_id:
            current_ckpt = wf[ckpt_node_id].get("inputs", {}).get("ckpt_name", "")
            resolved_ckpt = self._resolve_model_name(checkpoint, avail_ckpts)
            target_ckpt = resolved_ckpt

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

        # 1.5. Inject or Configure Custom UNet if requested
        model_source_node = ckpt_node_id
        clip_source_node = ckpt_node_id
        clip_source_slot = 1
        vae_source_node = ckpt_node_id
        vae_source_slot = 2

        numeric_ids = [int(k) for k in wf.keys() if k.isdigit()]
        is_anima = bool(unet and "anima" in unet.lower())

        if unet and unet.strip() and unet.lower() not in ("none", "default"):
            resolved_unet = self._resolve_model_name(unet, avail_unets) or unet
            existing_unets = [k for k, v in wf.items() if v.get("class_type") == "UNETLoader"]
            if existing_unets:
                wf[existing_unets[0]]["inputs"]["unet_name"] = resolved_unet
                model_source_node = existing_unets[0]
            else:
                unet_id = str(max(numeric_ids, default=50) + 1)
                numeric_ids.append(int(unet_id))
                wf[unet_id] = {
                    "class_type": "UNETLoader",
                    "inputs": {
                        "unet_name": resolved_unet,
                        "weight_dtype": "default"
                    },
                    "_meta": {"title": f"Load Custom UNet ({resolved_unet})"}
                }
                # Rewire any node that took model from ckpt_node_id to unet_id
                for nid, n in wf.items():
                    if nid in (unet_id, ckpt_node_id):
                        continue
                    for in_name, in_val in n.get("inputs", {}).items():
                        if isinstance(in_val, list) and len(in_val) >= 2:
                            if str(in_val[0]) == ckpt_node_id and in_val[1] == 0:
                                n["inputs"][in_name] = [unet_id, 0]
                model_source_node = unet_id
            logger.info(f"Using Custom UNet: {resolved_unet}")

        # 1.6. Architecture-specific handling (Anima, Flux, SDXL via model_preset or auto-detection)
        clip_candidates = []
        vae_candidates = []
        clip_type = "stable_diffusion"

        if model_preset and "defaults" in model_preset:
            p_def = model_preset["defaults"]
            clip_candidates = p_def.get("clip_candidates", [])
            vae_candidates = p_def.get("vae_candidates", [])
            clip_type = p_def.get("clip_type", "stable_diffusion")
        elif is_anima:
            clip_candidates = ["qwen_3_06b_base.safetensors", "jedpointreal_animaV1_txt.safetensors"]
            vae_candidates = [
                "qwen_image_vae.safetensors",
                "QwenImage\\qwen_image_vae.safetensors",
                "QwenImage/qwen_image_vae.safetensors",
                "qwen_vae.safetensors"
            ]

        if clip_candidates:
            avail_clips = available.get("clips", [])
            chosen_clip = next((c for c in clip_candidates if c in avail_clips or c.replace("/", "\\") in avail_clips), None)
            if not chosen_clip:
                chosen_clip = next((c for c in avail_clips if any(pat in c.lower() for pat in ["qwen_3_06", "anima"])), None)
            if not chosen_clip and avail_clips:
                chosen_clip = avail_clips[0]

            if chosen_clip:
                clip_loader_id = str(max(numeric_ids, default=60) + 1)
                numeric_ids.append(int(clip_loader_id))
                wf[clip_loader_id] = {
                    "class_type": "CLIPLoader",
                    "inputs": {
                        "clip_name": chosen_clip,
                        "type": clip_type
                    },
                    "_meta": {"title": f"Load Native Text Encoder ({chosen_clip})"}
                }
                # Rewire CLIP consumers from ckpt_node_id to clip_loader_id
                for nid, n in wf.items():
                    if nid == clip_loader_id:
                        continue
                    for in_name, in_val in n.get("inputs", {}).items():
                        if isinstance(in_val, list) and len(in_val) >= 2:
                            if str(in_val[0]) == ckpt_node_id and in_val[1] == 1:
                                n["inputs"][in_name] = [clip_loader_id, 0]
                clip_source_node = clip_loader_id
                clip_source_slot = 0
                logger.info(f"Using Native Text Encoder: {chosen_clip} for {model_preset.get('name') if model_preset else 'Anima'}")

        # Auto Native VAE if no custom VAE explicitly selected
        if (not vae or vae.lower() in ("default", "")) and vae_candidates:
            chosen_vae = next((v for v in vae_candidates if v in avail_vaes or v.replace("/", "\\") in avail_vaes), None)
            if not chosen_vae:
                chosen_vae = next((v for v in avail_vaes if "qwen" in v.lower()), None)
            if chosen_vae:
                vae_loader_id = str(max(numeric_ids, default=70) + 2)
                numeric_ids.append(int(vae_loader_id))
                wf[vae_loader_id] = {
                    "class_type": "VAELoader",
                    "inputs": {"vae_name": chosen_vae},
                    "_meta": {"title": f"Load Native VAE ({chosen_vae})"}
                }
                for nid, n in wf.items():
                    if n.get("class_type") == "VAEDecode":
                        n.setdefault("inputs", {})["vae"] = [vae_loader_id, 0]
                vae_source_node = vae_loader_id
                vae_source_slot = 0
                logger.info(f"Using Native Architecture VAE: {chosen_vae}")

        # Safe to decouple CheckpointLoader when custom UNet and Text Encoder take over all roles
        if clip_candidates and ckpt_node_id and ckpt_node_id in wf:
            wf.pop(ckpt_node_id, None)

        # 2. Inject or Configure LoRA if requested
        if lora and lora.strip() and lora.lower() != "none":
            resolved_lora = self._resolve_model_name(lora, avail_loras) or lora
            existing_loras = [k for k, v in wf.items() if v.get("class_type") == "LoraLoader"]
            if existing_loras:
                wf[existing_loras[0]]["inputs"]["lora_name"] = resolved_lora
                wf[existing_loras[0]]["inputs"]["strength_model"] = lora_strength
                wf[existing_loras[0]]["inputs"]["strength_clip"] = lora_strength
            else:
                lora_id = str(max(numeric_ids, default=100) + 1)
                numeric_ids.append(int(lora_id))
                wf[lora_id] = {
                    "class_type": "LoraLoader",
                    "inputs": {
                        "lora_name": resolved_lora,
                        "strength_model": lora_strength,
                        "strength_clip": lora_strength,
                        "model": [model_source_node, 0],
                        "clip": [clip_source_node, clip_source_slot]
                    },
                    "_meta": {"title": f"Load LoRA ({resolved_lora})"}
                }
                # Rewire nodes that connected to model_source_node model or clip_source to lora
                for nid, n in wf.items():
                    if nid in (lora_id, model_source_node, clip_source_node):
                        continue
                    for in_name, in_val in n.get("inputs", {}).items():
                        if isinstance(in_val, list) and len(in_val) >= 2:
                            if str(in_val[0]) == model_source_node and in_val[1] == 0:
                                n["inputs"][in_name] = [lora_id, 0]
                            elif str(in_val[0]) == clip_source_node and in_val[1] == clip_source_slot:
                                n["inputs"][in_name] = [lora_id, 1]
                logger.info(f"Injected LoRA: {resolved_lora} (strength: {lora_strength})")

        # 3. Inject or Configure Custom VAE if requested
        if vae and vae.strip() and vae.lower() != "default":
            resolved_vae = self._resolve_model_name(vae, avail_vaes) or vae
            existing_vaes = [k for k, v in wf.items() if v.get("class_type") == "VAELoader"]
            if existing_vaes:
                wf[existing_vaes[0]]["inputs"]["vae_name"] = resolved_vae
            else:
                vae_id = str(max(numeric_ids, default=200) + 2)
                numeric_ids.append(int(vae_id))
                wf[vae_id] = {
                    "class_type": "VAELoader",
                    "inputs": {"vae_name": resolved_vae},
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

        # 5. Handle Reference Image (img2img / frame-to-frame animation chaining)
        if reference_image:
            # Find active VAE connection
            vae_link = None
            for nid, n in wf.items():
                if n.get("class_type") == "VAEDecode":
                    vae_link = n.get("inputs", {}).get("vae")
                    if vae_link:
                        break
            if not vae_link:
                vae_link = [vae_source_node, vae_source_slot]

            load_img_id = str(max(numeric_ids, default=950) + 1)
            numeric_ids.append(int(load_img_id))
            wf[load_img_id] = {
                "class_type": "LoadImage",
                "inputs": {
                    "image": reference_image
                },
                "_meta": {"title": f"Load Frame Reference ({reference_image})"}
            }

            vae_enc_id = str(max(numeric_ids, default=950) + 1)
            numeric_ids.append(int(vae_enc_id))
            wf[vae_enc_id] = {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": [load_img_id, 0],
                    "vae": vae_link
                },
                "_meta": {"title": "Encode Reference Image to Latent"}
            }

            for k_id in ksampler_nodes:
                wf[k_id].setdefault("inputs", {})["latent_image"] = [vae_enc_id, 0]
                wf[k_id]["inputs"]["denoise"] = denoise
            logger.info(f"Injected Reference Image ({reference_image}) with denoise={denoise}")
        elif denoise < 1.0:
            for k_id in ksampler_nodes:
                wf[k_id].setdefault("inputs", {})["denoise"] = denoise

        # 6. BiRefNet AI Background Removal Injection (Movie Generator Pipeline)
        if remove_background:
            vae_decode_id = next((nid for nid, n in wf.items() if n.get("class_type") == "VAEDecode"), None)
            if vae_decode_id:
                bg_model_id = str(max(numeric_ids, default=880) + 1)
                numeric_ids.append(int(bg_model_id))
                wf[bg_model_id] = {
                    "class_type": "LoadBackgroundRemovalModel",
                    "inputs": {"bg_removal_name": "birefnet.safetensors"},
                    "_meta": {"title": "Load BiRefNet Background Model"}
                }

                rem_bg_id = str(max(numeric_ids, default=880) + 1)
                numeric_ids.append(int(rem_bg_id))
                wf[rem_bg_id] = {
                    "class_type": "RemoveBackground",
                    "inputs": {
                        "bg_removal_model": [bg_model_id, 0],
                        "image": [vae_decode_id, 0]
                    },
                    "_meta": {"title": "BiRefNet Remove Background"}
                }

                invert_id = str(max(numeric_ids, default=880) + 1)
                numeric_ids.append(int(invert_id))
                wf[invert_id] = {
                    "class_type": "InvertMask",
                    "inputs": {"mask": [rem_bg_id, 0]},
                    "_meta": {"title": "Invert Mask"}
                }

                join_alpha_id = str(max(numeric_ids, default=880) + 1)
                numeric_ids.append(int(join_alpha_id))
                wf[join_alpha_id] = {
                    "class_type": "JoinImageWithAlpha",
                    "inputs": {
                        "image": [vae_decode_id, 0],
                        "alpha": [invert_id, 0]
                    },
                    "_meta": {"title": "Join Image with Alpha (Transparent PNG)"}
                }

                # Rewire SaveImage nodes to output transparent RGBA image
                for nid, n in wf.items():
                    if n.get("class_type") == "SaveImage":
                        in_imgs = n.get("inputs", {}).get("images")
                        if isinstance(in_imgs, list) and len(in_imgs) >= 1 and str(in_imgs[0]) == str(vae_decode_id):
                            n["inputs"]["images"] = [join_alpha_id, 0]
                logger.info("Injected native BiRefNet Background Removal into generation pipeline.")

        return wf

    def remove_background_birefnet(self, image_bytes: bytes) -> bytes:
        """
        Executes high-fidelity BiRefNet AI background removal on the given image bytes via ComfyUI.
        Returns transparent RGBA PNG bytes.
        """
        uploaded_name = self.upload_image(image_bytes, filename="biref_input.png")
        wf = {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": uploaded_name}
            },
            "2": {
                "class_type": "LoadBackgroundRemovalModel",
                "inputs": {"bg_removal_name": "birefnet.safetensors"}
            },
            "3": {
                "class_type": "RemoveBackground",
                "inputs": {
                    "bg_removal_model": ["2", 0],
                    "image": ["1", 0]
                }
            },
            "4": {
                "class_type": "InvertMask",
                "inputs": {"mask": ["3", 0]}
            },
            "5": {
                "class_type": "JoinImageWithAlpha",
                "inputs": {
                    "image": ["1", 0],
                    "alpha": ["4", 0]
                }
            },
            "6": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "BiRefNet_Out",
                    "images": ["5", 0]
                }
            }
        }
        prompt_id = self.queue_prompt(wf)
        if not prompt_id:
            raise RuntimeError("Failed to queue BiRefNet prompt.")
        outputs = self.wait_for_completion(prompt_id)
        if not outputs:
            raise RuntimeError("BiRefNet execution timed out or failed.")
        fn, subf, ftype = outputs[0]
        return self.get_image_data(fn, subf, ftype)

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
