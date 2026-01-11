#!/usr/bin/env python3
"""
Test script for the post-processor framework.
Tests ASK processor with visual_mask, visual_edit, and zoom_in methods.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw
import numpy as np

# Test the post-processor framework
def test_postprocessor_framework():
    """Test the basic post-processor framework."""
    print("=" * 60)
    print("Testing Post-Processor Framework")
    print("=" * 60)
    
    # Test 1: Import modules
    print("\n[Test 1] Importing modules...")
    try:
        from post_processors import ProcessorRegistry, apply_postprocess, ASKProcessor
        from post_processors.utils import normalize_to_absolute_bbox
        print("✅ All modules imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Check registry
    print("\n[Test 2] Checking processor registry...")
    try:
        processors = ProcessorRegistry.list_processors()
        print(f"✅ Available processors: {processors}")
        assert "ask" in processors, "ASK processor not registered"
        assert "sd" in processors, "SD processor not registered"
    except Exception as e:
        print(f"❌ Registry check failed: {e}")
        return False
    
    # Test 3: Create a test image
    print("\n[Test 3] Creating test image...")
    try:
        # Create a simple test image with colored rectangles
        test_image = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(test_image)
        # Draw some colored rectangles to simulate objects
        draw.rectangle([50, 50, 150, 150], fill='red', outline='black')
        draw.rectangle([200, 100, 300, 200], fill='blue', outline='black')
        print("✅ Test image created (400x300 with 2 colored rectangles)")
    except Exception as e:
        print(f"❌ Image creation failed: {e}")
        return False
    
    # Test 4: Test bbox conversion utility
    print("\n[Test 4] Testing bbox conversion...")
    try:
        # Normalized bbox (0-1)
        norm_bbox = (0.125, 0.167, 0.25, 0.333)  # approximately (50, 50, 100, 100) in 400x300 image
        abs_bbox = normalize_to_absolute_bbox(norm_bbox, (400, 300))
        print(f"  Normalized: {norm_bbox}")
        print(f"  Absolute: {abs_bbox}")
        # Allow for rounding differences
        assert abs(abs_bbox[0] - 50) <= 1, f"X coordinate off: {abs_bbox[0]}"
        assert abs(abs_bbox[1] - 50) <= 1, f"Y coordinate off: {abs_bbox[1]}"
        assert abs(abs_bbox[2] - 100) <= 1, f"Width off: {abs_bbox[2]}"
        assert abs(abs_bbox[3] - 100) <= 1, f"Height off: {abs_bbox[3]}"
        print("✅ Bbox conversion works correctly")
    except Exception as e:
        print(f"❌ Bbox conversion failed: {e}")
        return False
    
    # Test 5: Test ASK processor - visual_mask
    print("\n[Test 5] Testing ASK processor - visual_mask...")
    try:
        config = {
            "method": "visual_mask",
            "mask_padding": 10,
        }
        processor = ASKProcessor(config)
        
        # Define test bboxes (normalized)
        bboxes = [
            (0.125, 0.167, 0.25, 0.333),  # First rectangle
            (0.5, 0.333, 0.25, 0.333),    # Second rectangle
        ]
        
        result = processor.process(test_image.copy(), bboxes, {"tool_name": "test"})
        assert result.size == test_image.size, "Image size changed"
        print("✅ visual_mask processing completed")
    except Exception as e:
        print(f"❌ visual_mask test failed: {e}")
        return False
    
    # Test 6: Test ASK processor - visual_edit
    print("\n[Test 6] Testing ASK processor - visual_edit...")
    try:
        config = {
            "method": "visual_edit",
            "inpaint_radius": 3,
        }
        processor = ASKProcessor(config)
        
        result = processor.process(test_image.copy(), bboxes, {"tool_name": "test"})
        assert result.size == test_image.size, "Image size changed"
        print("✅ visual_edit processing completed")
    except Exception as e:
        print(f"❌ visual_edit test failed: {e}")
        return False
    
    # Test 7: Test ASK processor - zoom_in
    print("\n[Test 7] Testing ASK processor - zoom_in...")
    try:
        config = {
            "method": "zoom_in",
            "zoom_padding": 0.05,
        }
        processor = ASKProcessor(config)
        
        result = processor.process(test_image.copy(), bboxes, {"tool_name": "test"})
        # Zoomed image should be smaller than original
        assert result.size != test_image.size, "Zoom didn't change image size"
        print(f"✅ zoom_in processing completed (new size: {result.size})")
    except Exception as e:
        print(f"❌ zoom_in test failed: {e}")
        return False
    
    # Test 8: Test apply_postprocess with disabled config
    print("\n[Test 8] Testing apply_postprocess with disabled config...")
    try:
        # Temporarily modify config
        from config import POST_PROCESSOR_CONFIG
        original_enabled = POST_PROCESSOR_CONFIG.get("enabled", False)
        POST_PROCESSOR_CONFIG["enabled"] = False
        
        result = apply_postprocess(test_image.copy(), bboxes, "test")
        assert result == test_image or np.array_equal(np.array(result), np.array(test_image)), \
            "Image was modified when post-processing disabled"
        
        # Restore config
        POST_PROCESSOR_CONFIG["enabled"] = original_enabled
        print("✅ Post-processing correctly disabled when config.enabled=False")
    except Exception as e:
        print(f"❌ Disabled config test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_postprocessor_framework()
    sys.exit(0 if success else 1)
