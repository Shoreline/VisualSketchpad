# VSP Post-Processing Framework

A general, extensible post-processing framework for VSP vision tools that supports multiple backends for image manipulation.

## Overview

This framework allows transparent post-processing of VSP vision tool outputs. The LLM sees modified images but doesn't need to know about the processing steps - it's completely transparent to the reasoning process.

## Architecture

```
VSP Vision Tool → Post-Processor → Modified Image → LLM
```

The post-processing happens inline within vision tools like `detection()` and `segment_and_mark()`, but is controlled via configuration.

## Supported Backends

### 1. ASK (Agent-ScanKit) - Local Processing

Three methods available:
- **visual_mask**: Draw black rectangles over detected regions
- **visual_edit**: Inpaint detected regions using OpenCV
- **zoom_in**: Crop and zoom into detected regions

### 2. Stable Diffusion - Remote API (Stub)

Future implementation for generative image editing via remote API.

## Configuration

Edit `/Users/yuantian/code/VisualSketchpad/agent/config.py`:

```python
POST_PROCESSOR_CONFIG = {
    "enabled": False,       # Set to True to enable
    "backend": "ask",       # "ask", "sd", or custom
    "save_before_image": True,  # Save image before post-processing
    
    # ASK-specific settings
    "ask": {
        "method": "visual_mask",  # "visual_mask", "visual_edit", "zoom_in"
        "mask_padding": 20,        # Pixels to expand mask beyond bbox
        "inpaint_radius": 3,       # OpenCV inpainting radius
        "zoom_padding": 0.05,      # Relative padding for zoom
    },
    
    # Stable Diffusion settings (future)
    "sd": {
        "endpoint": "http://localhost:7860",
        "method": "inpaint",
        "prompt": "remove detected objects",
        "strength": 0.8,
    },
}
```

### Before/After Image Saving

When `save_before_image: True` (default), the framework saves two images:

1. **Before**: `before_postproc_{tool_name}_{timestamp}.png`
   - The annotated image from VSP vision tool
   - Shows bounding boxes, labels, masks, etc.
   - NOT yet post-processed

2. **After**: The final displayed image (saved by Jupyter executor)
   - Post-processed version
   - What the LLM actually sees

This allows comparison between VSP's analysis and the post-processed result.

## Usage Examples

### Example 1: Mask Detected Objects

```python
# In config.py
POST_PROCESSOR_CONFIG = {
    "enabled": True,
    "backend": "ask",
    "ask": {
        "method": "visual_mask",
        "mask_padding": 30,
    }
}

# LLM's code (unchanged - no awareness of post-processing)
image = Image.open("sample.jpg")
output, boxes = detection(image, ["person", "car"])
display(output.annotated_image)  
# Shows image with detected regions masked in black
```

### Example 2: Inpaint Segmented Regions

```python
# In config.py
POST_PROCESSOR_CONFIG = {
    "enabled": True,
    "backend": "ask",
    "ask": {
        "method": "visual_edit",
        "inpaint_radius": 5,
    }
}

# LLM's code
output, boxes = segment_and_mark(image)
display(output.annotated_image)  
# Shows image with segmented regions inpainted
```

### Example 3: Zoom Into Detected Region

```python
# In config.py
POST_PROCESSOR_CONFIG = {
    "enabled": True,
    "backend": "ask",
    "ask": {
        "method": "zoom_in",
        "zoom_padding": 0.1,
    }
}

# LLM's code
output, boxes = detection(image, ["face"])
display(output.annotated_image)  
# Shows zoomed-in view of first detected face
```

## Adding Custom Processors

1. Create a new processor class inheriting from `PostProcessor`:

```python
# custom_processor.py
from .base import PostProcessor
from PIL import Image

class MyCustomProcessor(PostProcessor):
    def get_name(self) -> str:
        return "MyCustom"
    
    def process(self, image: Image.Image, bboxes, context):
        # Your custom processing logic
        return modified_image
```

2. Register it in `__init__.py`:

```python
from .custom_processor import MyCustomProcessor

class ProcessorRegistry:
    _processors = {
        "ask": ASKProcessor,
        "sd": SDProcessor,
        "custom": MyCustomProcessor,  # Add here
    }
```

3. Use it in config:

```python
POST_PROCESSOR_CONFIG = {
    "enabled": True,
    "backend": "custom",
    "custom": {
        # Your custom settings
    }
}
```

## Module Structure

```
post_processors/
├── __init__.py          # Main interface and registry
├── base.py              # PostProcessor abstract base class
├── ask_processor.py     # ASK implementation
├── sd_processor.py      # Stable Diffusion stub
├── utils.py             # Shared utilities
└── README.md            # This file
```

## Testing

Run the test suite:

```bash
cd /Users/yuantian/code/VisualSketchpad
source sketchpad_env/bin/activate
python agent/test_postprocessor.py
```

## Key Features

✅ **Transparent to LLM**: No prompt changes needed
✅ **Extensible**: Easy to add new processors
✅ **Flexible**: Each processor has its own configuration
✅ **Maintainable**: Clear separation of concerns
✅ **Future-proof**: Supports local and remote backends
✅ **Backward compatible**: Disabled by default

## Technical Details

### Bbox Format

VSP vision tools return normalized bounding boxes (0-1 range):
- Format: `(x, y, w, h)` where all values are in [0, 1]
- `x, y`: top-left corner coordinates
- `w, h`: width and height

The framework automatically converts these to absolute pixel coordinates when needed.

### Error Handling

If post-processing fails, the framework returns the original image and logs the error. This ensures VSP continues working even if post-processing encounters issues.

### Performance

- **ASK processors**: Local, fast (milliseconds)
- **SD processors**: Remote, slower (seconds) - future implementation

## Future Enhancements

- [ ] Implement Stable Diffusion processor
- [ ] Add more ASK methods (blur, pixelate, etc.)
- [ ] Support chaining multiple processors
- [ ] Add processor-specific logging and metrics
- [ ] Create processor plugin system
