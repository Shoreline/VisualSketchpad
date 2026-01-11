from .base import PostProcessor
from .ask_processor import ASKProcessor
from .sd_processor import SDProcessor

class ProcessorRegistry:
    _processors = {
        "ask": ASKProcessor,
        "sd": SDProcessor,
    }
    
    @classmethod
    def register(cls, name: str, processor_class):
        cls._processors[name] = processor_class
    
    @classmethod
    def get(cls, name: str, config: dict) -> PostProcessor:
        if name not in cls._processors:
            raise ValueError(f"Unknown processor: {name}")
        return cls._processors[name](config)
    
    @classmethod
    def list_processors(cls):
        return list(cls._processors.keys())


def apply_postprocess(image, bboxes, tool_name="unknown"):
    """
    Apply configured post-processing to vision tool output.
    This is the main entry point called by vision tools.
    
    Args:
        image: PIL Image or AnnotatedImage from vision tool
        bboxes: List of normalized (0-1) bboxes [(x, y, w, h), ...]
        tool_name: Name of the vision tool (for logging)
    
    Returns:
        Processed image (same type as input)
    """
    from config import POST_PROCESSOR_CONFIG
    import os
    
    # Check if post-processing is enabled
    if not POST_PROCESSOR_CONFIG.get("enabled", False):
        return image
    
    backend = POST_PROCESSOR_CONFIG.get("backend")
    if not backend:
        return image
    
    try:
        # Save the "before" image (annotated by VSP, before post-processing)
        # This allows comparison between VSP's output and post-processed result
        save_before = POST_PROCESSOR_CONFIG.get("save_before_image", True)
        if save_before:
            from tools import AnnotatedImage
            
            before_image = image.annotated_image if isinstance(image, AnnotatedImage) else image
            
            # Generate filename with tool name and timestamp for uniqueness
            import time
            timestamp = int(time.time() * 1000) % 1000000  # Last 6 digits of ms timestamp
            before_filename = f"before_postproc_{tool_name}_{timestamp}.png"
            
            # Use working directory from environment variable (set by Jupyter executor)
            working_dir = os.environ.get("VSP_WORKING_DIR")
            if working_dir:
                before_filepath = os.path.join(working_dir, before_filename)
            else:
                # Fall back to current directory if not set
                before_filepath = before_filename
                print(f"[POST_PROCESSOR_WARNING] VSP_WORKING_DIR not set, using current directory")
            
            try:
                before_image.save(before_filepath)
                print(f"[POST_PROCESSOR] Saved before image: {before_filepath}")
            except Exception as e:
                print(f"[POST_PROCESSOR] Warning: Could not save before image: {e}")
        
        # Get processor
        processor_config = POST_PROCESSOR_CONFIG.get(backend, {})
        processor = ProcessorRegistry.get(backend, processor_config)
        
        # Handle AnnotatedImage wrapper
        from tools import AnnotatedImage
        if isinstance(image, AnnotatedImage):
            # Process the annotated image
            processed = processor.process(
                image.annotated_image, 
                bboxes,
                {"tool_name": tool_name, "image_size": image.annotated_image.size}
            )
            # Return wrapped result
            return AnnotatedImage(processed, image.original_image)
        else:
            # Process regular PIL image
            return processor.process(
                image, 
                bboxes, 
                {"tool_name": tool_name, "image_size": image.size}
            )
    
    except Exception as e:
        print(f"[POST_PROCESSOR_ERROR] {e}")
        # Return original on error
        return image


# Export for easy imports
__all__ = ['PostProcessor', 'ProcessorRegistry', 'ASKProcessor', 'SDProcessor', 'apply_postprocess']
