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
