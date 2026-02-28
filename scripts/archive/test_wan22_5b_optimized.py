#!/usr/bin/env python3
"""
WAN 2.2 5B - Optimized for Best Quality
"""

import json
import requests
import time
import uuid

COMFYUI_URL = "http://127.0.0.1:8188"

def test_5b_optimized():
    """Optimize 5B with better settings for quality"""
    
    workflow = {
        "1": {  # CLIP Loader
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "type": "wan",
                "config": "default"
            }
        },
        "2": {  # VAE Loader (2.2 VAE for 5B)
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "wan2.2_vae.safetensors"
            }
        },
        "3": {  # UNET Loader (5B model)
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "wan2.2_ti2v_5B_fp16.safetensors",
                "weight_dtype": "default"
            }
        },
        "4": {  # Positive Prompt
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "A golden retriever running happily through a sunlit meadow, tail wagging, slow motion, cinematic lighting, high quality, detailed fur, beautiful natural environment, sharp focus, 4k quality",
                "clip": ["1", 0]
            }
        },
        "5": {  # Negative Prompt
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality, static, ugly, deformed, watermark, text, distorted, out of focus, soft, hazy, unclear, shadow artifacts",
                "clip": ["1", 0]
            }
        },
        "6": {  # Image to Video Latent
            "class_type": "Wan22ImageToVideoLatent",
            "inputs": {
                "width": 704,      # Optimal resolution per docs
                "height": 704,     # Square for better quality
                "length": 41,      # ~1.7 sec @ 24fps
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
        "8": {  # KSampler - OPTIMIZED
            "class_type": "KSampler",
            "inputs": {
                "seed": int(time.time()),
                "steps": 40,           # Increased from 20
                "cfg": 6.5,            # Increased from 5 for sharper output
                "sampler_name": "dpmpp_2m",  # Better sampler
                "scheduler": "karras", # Better scheduler
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
                "filename_prefix": "wan22_5b_OPTIMIZED",
                "codec": "vp9",
                "fps": 24,
                "crf": 16,
                "images": ["9", 0]
            }
        }
    }
    
    print("=" * 60)
    print("WAN 2.2 5B - OPTIMIZED Quality Settings")
    print("=" * 60)
    print("\nImprovements vs baseline:")
    print("- Resolution: 704x704 (was 512x512)")
    print("- Steps: 40 (was 20) - 2x more detail")
    print("- CFG: 6.5 (was 5.0) - sharper, less blur")
    print("- Sampler: dpmpp_2m (was uni_pc) - better quality")
    print("- Scheduler: karras (was simple) - smoother")
    print("- Frames: 41 (~1.7 sec)")
    print("\nPrompt: Golden retriever in meadow (optimized)")
    print("\nQueuing generation...")
    
    payload = {
        "prompt": workflow,
        "client_id": str(uuid.uuid4())
    }
    
    response = requests.post(
        f"{COMFYUI_URL}/prompt",
        json=payload
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        prompt_id = result.get("prompt_id")
        print(f"[SUCCESS] Queued! Prompt ID: {prompt_id}")
        print("\nETA: ~2-3 minutes (longer due to 40 steps + higher res)")
        print("Expected: Much sharper, less blur, better motion")
        return True
    else:
        print(f"[ERROR] Failed to queue")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    test_5b_optimized()
