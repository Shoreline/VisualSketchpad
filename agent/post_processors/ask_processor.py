from PIL import Image, ImageDraw
import cv2
import numpy as np
from typing import List, Tuple, Dict
from .base import PostProcessor
from .utils import normalize_to_absolute_bbox

class ASKProcessor(PostProcessor):
    """Agent-ScanKit processor for local image manipulation."""
    
    def get_name(self) -> str:
        return "ASK"
    
    def process(self, image: Image.Image, bboxes: List[Tuple], 
                context: Dict) -> Image.Image:
        method = self.config.get("method", "visual_mask")
        
        print(f"[POST_PROCESSOR] ASK:{method}")
        
        if method == "visual_mask":
            return self._apply_visual_mask(image, bboxes, context)
        elif method == "visual_edit":
            return self._apply_visual_edit(image, bboxes, context)
        elif method == "zoom_in":
            return self._apply_zoom_in(image, bboxes, context)
        else:
            return image
    
    def _apply_visual_mask(self, image, bboxes, context):
        """Draw black rectangles over detected regions."""
        # Make a copy to avoid modifying original
        image = image.copy()
        draw = ImageDraw.Draw(image)
        padding = self.config.get("mask_padding", 20)
        w, h = image.size
        
        for bbox in bboxes:
            x, y, bw, bh = normalize_to_absolute_bbox(bbox, (w, h))
            draw.rectangle(
                [x-padding, y-padding, x+bw+padding, y+bh+padding],
                fill="black"
            )
        return image
    
    def _apply_visual_edit(self, image, bboxes, context):
        """Inpaint detected regions using OpenCV."""
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        mask = np.zeros(image_cv.shape[:2], dtype=np.uint8)
        radius = self.config.get("inpaint_radius", 3)
        w, h = image.size
        
        for bbox in bboxes:
            x, y, bw, bh = normalize_to_absolute_bbox(bbox, (w, h))
            mask[int(y):int(y+bh), int(x):int(x+bw)] = 255
        
        result = cv2.inpaint(image_cv, mask, radius, cv2.INPAINT_TELEA)
        return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    
    def _apply_zoom_in(self, image, bboxes, context):
        """Crop and zoom into first detected region."""
        if not bboxes:
            return image
        
        padding = self.config.get("zoom_padding", 0.05)
        bbox = bboxes[0]
        x, y, bw, bh = bbox
        
        # Add padding
        x = max(0, x - padding)
        y = max(0, y - padding)
        bw = min(1 - x, bw + 2*padding)
        bh = min(1 - y, bh + 2*padding)
        
        w, h = image.size
        return image.crop((x*w, y*h, (x+bw)*w, (y+bh)*h))
