# LM Studio Integration & Prompt Engineering

**GameAssetGenerator** integrates with local **LM Studio** instances for AI prompt refinement, perspective alignment, and multi-step animation keyframe breakdowns.

---

## 1. Setting Up LM Studio

1. Open LM Studio on your system.
2. Load any preferred instruction-tuned LLM (e.g. *Mistral 7B Instruct*, *Llama 3*, *Qwen 2.5*, or *Phi-3*).
3. Navigate to the **Local Server** tab (`<->` icon).
4. Click **Start Server**.
5. The default endpoint is `http://127.0.0.1:1234/v1` (configurable in `settings/config.json`).
6. The web interface header will turn green: `LM Studio: Ready`.

---

## 2. In-App AI Capabilities

### 2.1 Prompt Enhancement ("✨ Enhance with AI")
- Type a simple concept: `Dwarf warrior with a golden hammer`.
- The generator dispatches the query with the selected perspective (e.g. Isometric) and style (e.g. 16-Bit Pixel Art) to LM Studio.
- LM Studio returns an optimized Stable Diffusion prompt complete with negative prompts and isolation constraints.

### 2.2 Keyframe Planning ("🤖 AI Keyframe Plan")
- For motions like **Walk**, **Sit Down**, or **Jump**, LM Studio analyzes the requested step count and generates distinct anatomical keyframe instructions (e.g. contact pose, recoil, passing, apex, landing).

---

## 3. Seamless Offline Fallback

If LM Studio is not currently running, the generator does not fail.
`lib/lm_client.py` seamlessly falls back to pre-defined animation templates in `prompts/animation_breakdowns.json` and `settings/animations.json`.
