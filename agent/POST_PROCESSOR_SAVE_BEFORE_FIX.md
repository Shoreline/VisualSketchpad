# Post-Processor "Save Before" Image Fix

## Problem

When VSP post-processing was enabled, the "before" images (VSP's annotated images before post-modification) were being saved to the wrong directory (`/Users/yuantian/code/VisualSketchpad/agent/`) instead of the task output directory alongside the post-modified images.

## Root Cause

The post-processor code couldn't access the correct output directory because:
1. `os.getcwd()` returned the VSP agent directory, not the task directory
2. Global variables in `config.py` couldn't be reliably shared across module imports
3. The Jupyter executor's `output_dir` parameter sets where it saves files, but doesn't change the current working directory of the Python process

## Solution

Set an environment variable `VSP_WORKING_DIR` when the Jupyter executor is initialized, which the post-processor can then read to determine the correct save location.

### Changes Made

#### 1. `/Users/yuantian/code/VisualSketchpad/agent/execution.py`

Set environment variable in `CodeExecutor.__init__`:

```python
self.working_dir = working_dir

if not os.path.exists(self.working_dir):
    os.makedirs(self.working_dir, exist_ok=True)
    
# Set environment variable for post-processors to access working directory
os.environ["VSP_WORKING_DIR"] = self.working_dir
    
# set up the server
self.server = LocalJupyterServer()
```

#### 2. `/Users/yuantian/code/VisualSketchpad/agent/post_processors/__init__.py`

Read the environment variable in `apply_postprocess`:

```python
# Use working directory from environment variable (set by Jupyter executor)
working_dir = os.environ.get("VSP_WORKING_DIR")
if working_dir:
    before_filepath = os.path.join(working_dir, before_filename)
else:
    # Fall back to current directory if not set
    before_filepath = before_filename
    print(f"[POST_PROCESSOR_WARNING] VSP_WORKING_DIR not set, using current directory")
```

## Result

"Before" images are now correctly saved in the task output directory:

```
output/job_XXX/details/vsp_*/category/task_id/output/input/
├── image_0.jpg                          # Original input
├── before_postproc_detection_*.png      # VSP-annotated (before post-processing) ✅
└── <hash>.png                           # Post-modified (after masking/inpainting/zoom)
```

## Verification

Test command:
```bash
cd /Users/yuantian/code/Mediator
python request.py --provider comt_vsp --model "qwen/qwen3-vl-235b-a22b-instruct" \
  --comt_sample_id deletion-0107 --max_tasks 1 \
  --vsp_postproc --vsp_postproc_method visual_mask --skip_eval
```

Check output:
```bash
ls -lh output/job_*/details/vsp_*/08-Political_Lobbying/0/output/input/ | grep before
```

Expected: Multiple `before_postproc_detection_*.png` files in the correct directory.

## Date

2026-01-10
