# som_server.py
import io
import base64
import json
from typing import List, Dict, Any

import numpy as np
from PIL import Image
import gradio as gr
import torch

# ====== Semantic-SAM imports ======
from semantic_sam.BaseModel import BaseModel
from semantic_sam import build_model
from semantic_sam.utils.arguments import load_opt_from_config_file
from inference_semsam_m2m_auto import inference_semsam_m2m_auto
# ===================================

# --------- 配置与模型加载 ----------
semsam_cfg = "semantic_sam_only_sa-1b_swinL.yaml"
semsam_ckpt = "swinl_only_sam_many2many.pth"
opt_semsam = load_opt_from_config_file(semsam_cfg)

# 构建与加载权重（需要 GPU）
model_semsam = BaseModel(opt_semsam, build_model(opt_semsam)).from_pretrained(semsam_ckpt).eval().cuda()
# ----------------------------------


# -------------- 工具函数 --------------
def _to_pil(x: Any) -> Image.Image:
    """把 numpy / PIL 统一成 PIL.Image"""
    if isinstance(x, Image.Image):
        return x
    if isinstance(x, np.ndarray):
        if x.dtype != np.uint8:
            x = x.astype(np.uint8)
        if x.ndim == 2:
            return Image.fromarray(x, "L")
        return Image.fromarray(x)
    raise TypeError(f"Unsupported image type: {type(x)}")

def _to_uint8_mask(arr: np.ndarray) -> np.ndarray:
    """将 bool/float/int 的 2D/3D mask 统一成 uint8 (0/255)"""
    if hasattr(arr, "detach"):  # torch.Tensor
        arr = arr.detach().cpu().numpy()
    if arr.dtype == bool:
        arr = arr.astype(np.uint8) * 255
    elif np.issubdtype(arr.dtype, np.integer):
        arr = (arr != 0).astype(np.uint8) * 255
    else:
        arr = (arr > 0.5).astype(np.uint8) * 255
    if arr.ndim == 3 and arr.shape[2] == 1:
        arr = arr[:, :, 0]
    return arr

def _mask_bbox(bin_mask: np.ndarray):
    """从二值 mask 计算 bbox=[x,y,w,h] 和 area"""
    ys, xs = np.where(bin_mask > 0)
    if len(xs) == 0:
        return [0, 0, 0, 0], 0
    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()
    bbox = [int(x1), int(y1), int(x2 - x1 + 1), int(y2 - y1 + 1)]
    area = int((bin_mask > 0).sum())
    return bbox, area

def _png_base64(mask_uint8_2d_or_3d: np.ndarray) -> str:
    """将 2D/3D uint8 mask 编成 PNG base64（不带 data: 前缀）"""
    if mask_uint8_2d_or_3d.ndim == 2:
        pil = Image.fromarray(mask_uint8_2d_or_3d, "L")
    elif mask_uint8_2d_or_3d.ndim == 3 and mask_uint8_2d_or_3d.shape[2] in (3, 4):
        pil = Image.fromarray(mask_uint8_2d_or_3d)
    else:
        pil = Image.fromarray(mask_uint8_2d_or_3d.squeeze(), "L")
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")

def _build_regions_from_mask(mask_obj: Any) -> List[Dict[str, Any]]:
    """
    将推理返回的 mask 转成“每个编号区域”的列表。
    兼容几种常见形式：
      - list[dict]，其中 dict 里含 'segmentation'（布尔/0-1 矩阵）和可选 'score'/'label'
      - 2D 整型 label map（0=背景，1..K 为区域 id）
      - 2D 布尔：只有一个区域
      - torch.Tensor：自动转 numpy 继续处理
    """
    regions: List[Dict[str, Any]] = []

    # 1) list[dict]：每个 item 表示一个区域
    if isinstance(mask_obj, (list, tuple)) and len(mask_obj) > 0 and isinstance(mask_obj[0], dict):
        for i, item in enumerate(mask_obj, start=1):
            seg = item.get("segmentation", None)
            if seg is None:
                continue
            seg = np.array(seg)
            bin_u8 = _to_uint8_mask(seg)
            bbox, area = _mask_bbox(bin_u8)
            regions.append({
                "id": int(item.get("id", i)),
                "category": item.get("category") or item.get("label") or None,
                "score": (float(item["score"]) if "score" in item else None),
                "area": area,
                "bbox": bbox,  # [x,y,w,h]
                "mask_png_base64": _png_base64(bin_u8),
                "height": int(bin_u8.shape[0]),
                "width": int(bin_u8.shape[1]),
            })
        return regions

    # 2) 2D 整型 label map：按 unique id 切分
    if isinstance(mask_obj, np.ndarray) and mask_obj.ndim == 2 and np.issubdtype(mask_obj.dtype, np.integer):
        labels = np.unique(mask_obj)
        labels = labels[labels != 0]  # 去掉背景 0
        for lid in labels.tolist():
            bin_u8 = ((mask_obj == lid).astype(np.uint8) * 255)
            bbox, area = _mask_bbox(bin_u8)
            regions.append({
                "id": int(lid),
                "category": None,
                "score": None,
                "area": area,
                "bbox": bbox,
                "mask_png_base64": _png_base64(bin_u8),
                "height": int(bin_u8.shape[0]),
                "width": int(bin_u8.shape[1]),
            })
        return regions

    # 3) 2D 布尔：视为单区域
    if isinstance(mask_obj, np.ndarray) and mask_obj.ndim == 2 and mask_obj.dtype == bool:
        bin_u8 = _to_uint8_mask(mask_obj)
        bbox, area = _mask_bbox(bin_u8)
        return [{
            "id": 1,
            "category": None,
            "score": None,
            "area": area,
            "bbox": bbox,
            "mask_png_base64": _png_base64(bin_u8),
            "height": int(bin_u8.shape[0]),
            "width": int(bin_u8.shape[1]),
        }]

    # 4) torch.Tensor：转 numpy 后重用逻辑
    if torch.is_tensor(mask_obj):
        return _build_regions_from_mask(mask_obj.detach().cpu().numpy())

    # 兜底：未知类型
    return [{"warning": f"unsupported mask type: {type(mask_obj).__name__}"}]
# -------------- 工具函数到此 --------------


@torch.no_grad()
def inference(image: Image.Image, slider: float, alpha: float, label_mode: str, anno_mode: List[str], *args, **kwargs):
    """封装一次推理，返回 (可视化图, 原始mask对象)"""
    _image = image.convert("RGB")

    # slider -> level（沿用你原始的阈值逻辑）
    if slider < 1.5 + 0.14:
        level = [1]
    elif slider < 1.5 + 0.28:
        level = [2]
    elif slider < 1.5 + 0.42:
        level = [3]
    elif slider < 1.5 + 0.56:
        level = [4]
    elif slider < 1.5 + 0.70:
        level = [5]
    elif slider < 1.5 + 0.84:
        level = [6]
    else:
        level = [6, 1, 2, 3, 4, 5]

    label_mode = 'a' if label_mode == 'Alphabet' else '1'

    text_size, hole_scale, island_scale = 640, 100, 100
    text, text_part, text_thresh = '', '', '0.0'

    with torch.autocast(device_type='cuda', dtype=torch.float16):
        output, mask = inference_semsam_m2m_auto(
            model_semsam, _image, level, text, text_part, text_thresh,
            text_size, hole_scale, island_scale, False,
            label_mode=label_mode, alpha=alpha, anno_mode=anno_mode,
            *args, **kwargs
        )

    # output 统一成 PIL，mask 原样返回给上层做结构化转换
    return _to_pil(output), mask


def gradio_interface(image, slider, alpha, label_mode, anno_mode):
    # Handle None values with defaults (important for API calls)
    if slider is None:
        slider = 1.8
    if alpha is None:
        alpha = 0.1
    if label_mode is None:
        label_mode = "Number"
    if anno_mode is None:
        anno_mode = ["Mask", "Mark"]
    
    vis_img, raw_mask = inference(image, slider, alpha, label_mode, anno_mode)

    # 关键：将 raw_mask 转为“每个编号区域”的结构化列表
    try:
        regions = _build_regions_from_mask(raw_mask)
    except Exception as e:
        regions = [{"error": f"{type(e).__name__}: {e}"}]

    return vis_img, regions


# ----------------- Gradio 接口 -----------------
demo = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.Image(type="pil", label="image"),
        gr.Number(value=1.8, label="slider"),
        gr.Number(value=0.1, label="alpha"),
        gr.Radio(["Number", "Alphabet"], value="Number", label="label_mode"),
        gr.CheckboxGroup(["Mask", "Box", "Mark"], value=["Mask", "Mark"], label="anno_mode"),
    ],
    outputs=[
        gr.Image(type="pil", label="segmentation"),
        gr.JSON(label="regions (per segment metadata)"),
    ],
    # 避免巨大 JSON 触发内置 CSV flagging 限制
    flagging_mode="never",
    # Disable caching to avoid state issues between requests
    cache_examples=False,
)

# Force serial processing to prevent state corruption from concurrent requests
# This prevents tensor dimension mismatches caused by thread-unsafe model operations
# Multiple requests can queue up, but only 1 will be processed at a time
demo.queue(
    concurrency_count=1    # KEY: Process only 1 request at a time (prevents state corruption)
    # Note: In Gradio 3.x, use concurrency_count; in Gradio 4.x, use default_concurrency_limit
)

# 在服务器上建议 0.0.0.0；需要公网临时链接就把 share=True
demo.launch(
    share=True, 
    server_name="0.0.0.0", 
    server_port=7862
    # Note: max_threads defaults to 40, which is fine
    # The key protection is default_concurrency_limit=1 above
)
# ------------------------------------------------

