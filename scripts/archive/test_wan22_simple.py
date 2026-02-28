#!/usr/bin/env python3
"""
Simplified WAN 2.2 test using ComfyUI API format
"""

import json
import requests
import time
import uuid

COMFYUI_URL = "http://127.0.0.1:8188"

def test_simple():
    """Minimal workflow test"""
    
    # Build minimal WAN 2.2 workflow in API format
    workflow = {
        "1": {  # CLIP Loader
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "type": "wan",
                "config": "default"
            }
        },
        "2": {  # VAE Loader
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "wan2.2_vae.safetensors"
            }
        },
        "3": {  # UNET Loader
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "wan2.2_ti2v_5B_fp16.safetensors",
                "weight_dtype": "default"
            }
        },
        "4": {  # Positive Prompt
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "A golden retriever running happily in a meadow, cinematic",
                "clip": ["1", 0]
            }
        },
        "5": {  # Negative Prompt
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality, static",
                "clip": ["1", 0]
            }
        },
        "6": {  # Image to Video Latent
            "class_type": "Wan22ImageToVideoLatent",
            "inputs": {
                "width": 512,
                "height": 512,
                "length": 25,
                "batch_size": 1,
                "vae": ["2", 0]
            }
        },
        "7": {  # Model Sampling
            "class_type": "ModelSamplingSD3",
            "inputs": {
                "shift": 8.0,
                "model": ["3", 0]
            }
        },
        "8": {  # KSampler
            "class_type": "KSampler",
            "inputs": {
                "seed": int(time.time()),
                "steps": 20,
                "cfg": 5.0,
                "sampler_name": "uni_pc",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["7", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0]
            }
        },
        "9": {  # VAE Decode
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["8", 0],
                "vae": ["2", 0]
            }
        },
        "10": {  # Save WEBM
            "class_type": "SaveWEBM",
            "inputs": {
                "filename_prefix": "wan22_test",
                "codec": "vp9",
                "fps": 24,
                "crf": 16,
                "images": ["9", 0]
            }
        }
    }
    
    print("Testing WAN 2.2 with minimal workflow...")
    print("Prompt: Golden retriever in meadow")
    print("Resolution: 512x512, 25 frames")
    
    # Send to API
    payload = {
        "prompt": workflow,
        "client_id": str(uuid.uuid4())
    }
    
    response = requests.post(
        f"{COMFYUI_URL}/prompt",
        json=payload
    )
    
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        prompt_id = result.get("prompt_id")
        print(f"\n[SUCCESS] Queued! Prompt ID: {prompt_id}")
        print("Check ComfyUI server logs for progress...")
        print("Video will be saved to: ComfyUI/output/")
        return True
    else:
        print(f"\n[ERROR] Failed to queue")
        return False

if __name__ == "__main__":
    test_simple()
