# -*- coding: utf-8 -*-
"""composition_preserve.py - 本地 ControlNet 构图保持生图

原理：对原图做 Canny 边缘检测 → 作为 ControlNet 条件 →
Stable Diffusion 在"保持原图构图（摆盘/视角/餐具位置）"的前提下，
按改造 Prompt 生成"健康版"菜品图。
"""
import logging
from functools import lru_cache
from pathlib import Path


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_MODEL_DIR = BASE_DIR / "models" / "base_dreamshaper"
CONTROLNET_DIR = BASE_DIR / "models" / "controlnet_canny"


@lru_cache(maxsize=1)
def _get_pipe():
    import torch
    from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

    if not BASE_MODEL_DIR.exists() or not CONTROLNET_DIR.exists():
        raise FileNotFoundError(
            "未找到本地模型，请先运行 models/download_models.py 下载 SD + ControlNet 模型"
        )

    controlnet = ControlNetModel.from_pretrained(str(CONTROLNET_DIR), torch_dtype=torch.float16)
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        str(BASE_MODEL_DIR),
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
        variant="fp16",
    )
    # 8GB 显存优化：组件按需搬上 GPU
    pipe.enable_model_cpu_offload()
    pipe.enable_attention_slicing()
    logger.info("ControlNet 管线已加载（dreamshaper-8 + canny）")
    return pipe


def _canny_edges(image: Image.Image, low: int = 100, high: int = 200) -> Image.Image:
    from PIL import Image
    import cv2
    import numpy as np

    arr = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, low, high)
    return Image.fromarray(edges).convert("RGB")


def generate_with_composition(
    original_image_path: str,
    prompt: str,
    out_path: str,
    negative_prompt: str = "low quality, blurry, deformed, extra limbs, watermark, text, logo, cartoon",
    num_steps: int = 25,
    guidance_scale: float = 7.0,
    controlnet_conditioning_scale: float = 0.85,
    seed: int = -1,
) -> str:
    from PIL import Image
    """保持原图构图地生成"健康版"菜品图。"""
    import torch

    pipe = _get_pipe()
    init = Image.open(original_image_path).convert("RGB")

    # 缩放到 SD 分辨率（短边 640，长边保持比例并取 8 的倍数）
    w, h = init.size
    target = 640
    ratio = target / min(w, h)
    if ratio < 1:
        w, h = int(w * ratio), int(h * ratio)
    w, h = (w // 8) * 8, (h // 8) * 8
    init = init.resize((w, h), Image.LANCZOS)

    edges = _canny_edges(init)

    generator = torch.Generator(device="cuda").manual_seed(seed) if seed >= 0 else None
    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=edges,
        num_inference_steps=num_steps,
        guidance_scale=guidance_scale,
        controlnet_conditioning_scale=controlnet_conditioning_scale,
        generator=generator,
    ).images[0]

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    result.save(out_path)
    logger.info("ControlNet 生图完成 -> %s", out_path)
    return out_path
