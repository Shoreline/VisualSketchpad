import gradio as gr
import cv2
import numpy as np
import os
import io
import base64
from PIL import Image
import torch
import torch.nn.functional as F
from torchvision.transforms import Compose

from depth_anything.dpt import DepthAnything
from depth_anything.util.transform import Resize, NormalizeImage, PrepareForNet


transform = Compose([
        Resize(
            width=518,
            height=518,
            resize_target=False,
            keep_aspect_ratio=True,
            ensure_multiple_of=14,
            resize_method='lower_bound',
            image_interpolation_method=cv2.INTER_CUBIC,
        ),
        NormalizeImage(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        PrepareForNet(),
])

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
model = DepthAnything.from_pretrained('LiheYoung/depth_anything_vitl14').to(DEVICE).eval()


def _image_to_base64(img: np.ndarray) -> str:
    """Convert numpy array image to PNG base64 string (without data: prefix)"""
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)
    pil_img = Image.fromarray(img)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def predict_depthmap(image):
    original_image = image.copy()

    h, w = image.shape[:2]

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) / 255.0
    image = transform({'image': image})['image']
    image = torch.from_numpy(image).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        depth = model(image)
    depth = F.interpolate(depth[None], (h, w), mode='bilinear', align_corners=False)[0, 0]
    
    # Store min/max before normalization for metadata
    depth_min = float(depth.min())
    depth_max = float(depth.max())
    
    depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
    depth = depth.cpu().numpy().astype(np.uint8)
    colored_depth = cv2.applyColorMap(depth, cv2.COLORMAP_INFERNO)[:, :, ::-1]
    
    # Convert to PIL for Gradio display
    colored_depth_pil = Image.fromarray(colored_depth)
    
    # Build JSON-serializable structure for LLM consumption
    depth_data = {
        "height": int(h),
        "width": int(w),
        "depth_min": depth_min,
        "depth_max": depth_max,
        "depth_map_grayscale_base64": _image_to_base64(depth),  # Raw normalized depth
        "depth_map_colored_base64": _image_to_base64(colored_depth),  # Colored visualization
    }
    
    return colored_depth_pil, depth_data


demo = gr.Interface(fn=predict_depthmap, 
                    inputs=[
                        gr.Image(label="image")
                    ],
                    outputs=[
                        gr.Image(type="pil", label="depth_map_visualization"),
                        gr.JSON(label="depth_data")
                    ]
                    )

# Force serial processing to prevent state corruption from concurrent requests
# This prevents tensor dimension mismatches caused by thread-unsafe model operations
# Multiple requests can queue up, but only 1 will be processed at a time
demo.queue(
    concurrency_count=1    # KEY: Process only 1 request at a time (prevents state corruption)
    # Note: In Gradio 3.x, use concurrency_count; in Gradio 4.x, use default_concurrency_limit
)
                    
demo.launch(
    share=True, 
    server_name="0.0.0.0", 
    server_port=7861, 
    show_api=True
    # Note: max_threads defaults to 40, which is fine
    # The key protection is default_concurrency_limit=1 above
)



