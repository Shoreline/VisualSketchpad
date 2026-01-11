from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from PIL import Image

class PostProcessor(ABC):
    """Abstract base class for VSP post-processors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def process(self, image: Image.Image, bboxes: List[Tuple[float, float, float, float]], 
                context: Dict[str, Any]) -> Image.Image:
        """
        Process image with detected bounding boxes.
        
        Args:
            image: PIL Image (may be annotated)
            bboxes: List of normalized (0-1) bboxes [(x, y, w, h), ...]
            context: Additional context (tool_name, image_size, etc.)
        
        Returns:
            Processed PIL Image
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return processor name for logging."""
        pass
