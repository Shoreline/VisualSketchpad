import os

# set up the agent
MAX_REPLY = 10

# set up the LLM for the agent
#os.environ['OPENAI_API_KEY'] = '[YOUR OPENAI API KEY]'
os.environ["AUTOGEN_USE_DOCKER"] = "False"

# Original OpenAI configuration (commented out)
# llm_config={
#     "cache_seed": None, 
#     "config_list": [
#         {
#             "model": "gpt-5", 
#             "api_key": os.environ.get("OPENAI_API_KEY")
#         }
#     ]
# }

# OpenRouter configuration (current)
llm_config={
    "cache_seed": None, 
    "config_list": [
        {
            # OpenRouter configuration
            #"model": "qwen/qwen3-vl-235b-a22b-instruct",  # Or any model from OpenRouter
            #"model": "google/gemini-2.5-flash",
            'model': "openai/gpt-5",
            #"model": "opengvlab/internvl3-78b",
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
            "base_url": "https://openrouter.ai/api/v1",
            
            # Optional: Add these headers for better tracking
            "api_type": "openai",  # OpenRouter is OpenAI-compatible
            # "extra_body": {
            #     "headers": {
            #         "HTTP-Referer": "https://your-site.com",  # Optional
            #         "X-Title": "VisualSketchpad"  # Optional
            #     }
            # }
        }
    ]
}

# use this after building your own server. You can also set up the server in other machines and paste them here.
SOM_ADDRESS = "http://34.210.214.193:7862"
GROUNDING_DINO_ADDRESS = "http://34.210.214.193:7860"
DEPTH_ANYTHING_ADDRESS = "http://34.210.214.193:7861"

# Post-Processing Configuration (Transparent to LLM)
# The LLM sees modified images but doesn't need to know about the processing steps
# 
# Can be controlled via environment variables (set by Mediator):
#   VSP_POSTPROC_ENABLED: "1" or "0"
#   VSP_POSTPROC_BACKEND: "ask" or "sd"
#   VSP_POSTPROC_METHOD: "visual_mask", "visual_edit", or "zoom_in"

# Read from environment variables if set, otherwise use defaults
_postproc_enabled = os.environ.get("VSP_POSTPROC_ENABLED", "0") == "1"
_postproc_backend = os.environ.get("VSP_POSTPROC_BACKEND", "ask")
_postproc_method = os.environ.get("VSP_POSTPROC_METHOD", "visual_mask")

POST_PROCESSOR_CONFIG = {
    "enabled": _postproc_enabled,  # Master switch for post-processing
    "backend": _postproc_backend,  # "ask", "sd", "custom", etc.
    "save_before_image": True,     # Save image before post-processing for comparison
    
    # ASK (Agent-ScanKit) - Local image manipulation
    "ask": {
        "method": _postproc_method,  # "visual_mask", "visual_edit", "zoom_in"
        "mask_padding": 20,           # Pixels to expand mask beyond bbox
        "inpaint_radius": 3,          # OpenCV inpainting radius
        "zoom_padding": 0.05,         # Relative padding for zoom
    },
    
    # Stable Diffusion - Remote generative editing (future)
    "sd": {
        "endpoint": "http://localhost:7860",
        "method": "inpaint",
        "prompt": "remove detected objects",
        "strength": 0.8,
    },
}
