from typing import Tuple

def normalize_to_absolute_bbox(bbox: Tuple[float, float, float, float], 
                               image_size: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """
    Convert normalized (0-1) bbox to absolute pixel coordinates.
    
    Args:
        bbox: (x, y, w, h) in range [0, 1]
        image_size: (width, height) in pixels
    
    Returns:
        (x, y, w, h) in absolute pixels
    """
    x, y, w, h = bbox
    img_w, img_h = image_size
    return (int(x * img_w), int(y * img_h), 
            int(w * img_w), int(h * img_h))
