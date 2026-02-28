#!/usr/bin/env python3
"""
Test WAN 2.2 14B model (higher quality, requires more VRAM)
"""

import json
import requests
import time
import uuid

COMFYUI_URL = "http://127.0.0.1:8188"

def test_14b():
    """Test 14B model with high+low noise workflow"""
    
    # Build 14B workflow - requires both high and low noise models
    workflow = {
        "1": {  # CLIP Loader
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "type": "wan",
                "config": "default"
            }
        },
        "2": {  # VAE Loader (2.1 VAE for 14B)
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "wan_2.1_vae.safetensors"
            }
        },
        "3": {  # High Noise UNET
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
                "weight_dtype": "default"
            }
        },
        "4": {  # Low Noise UNET
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors",
                "weight_dtype": "default"
            }
        },
        "5": {  # Positive Prompt
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "A golden retriever running happily through a sunlit meadow, tail wagging, slow motion, cinematic lighting, high quality, detailed fur",
                "clip": ["1", 0]
            }
        },
        "6": {  # Negative Prompt
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality, static, ugly, deformed, watermark",
                "clip": ["1", 0]
            }
        },
        "7": {  # Image to Video Latent
            "class_type": "Wan22ImageToVideoLatent",
            "inputs": {
                "width": 512,
                "height": 512,
                "length": 25,
                "batch_size": 1,
                "vae": ["2", 0]
            }
        },
        "8": {  # Model Sampling (High Noise)
            "class_type": "ModelSamplingSD3",
            "inputs": {
                "shift": 8.0,
                "model": ["3", 0]
            }
        },
        "9": {  # KSampler (High Noise Pass)
            "class_type": "KSampler",
            "inputs": {
                "seed": int(time.time()),
                "steps": 15,
                "cfg": 5.0,
                "sampler_name": "uni_pc",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["8", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["7", 0]
            }
        },
        "10": {  # Model Sampling (Low Noise)
            "class_type": "ModelSamplingSD3",
            "inputs": {
                "shift": 8.0,
                "model": ["4", 0]
            }
        },
        "11": {  # KSampler (Low Noise Pass - refinement)
            "class_type": "KSampler",
            "inputs": {
                "seed": int(time.time()),
                "steps": 15,
                "cfg": 5.0,
                "sampler_name": "uni_pc",
                "scheduler": "simple",
                "denoise": 0.5,
                "model": ["10", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["9", 0]
            }
        },
        "12": {  # VAE Decode
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["11", 0],
                "vae": ["2", 0]
            }
        },
        "13": {  # Save WEBM
            "class_type": "SaveWEBM",
            "inputs": {
                "filename_prefix": "wan22_14b_test",
                "codec": "vp9",
                "fps": 24,
                "crf": 16,
                "images": ["12", 0]
            }
        }
    }
    
    print("=" * 60)
    print("Testing WAN 2.2 14B Model")
    print("=" * 60)
    print("\nPrompt: Golden retriever in meadow (enhanced)")
    print("Resolution: 512x512, 25 frames")
    print("Two-pass generation: High noise (15 steps) + Low noise (15 steps)")
    print("\nWARNING: This will use ~18-20GB VRAM (you have 16.3GB)")
    print("If OOM occurs, will fall back to optimizing 5B model.")
    print("\nQueuing generation...")
    
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
    
    if response.status_code == 200:
        result = response.json()
        prompt_id = result.get("prompt_id")
        print(f"[SUCCESS] Queued! Prompt ID: {prompt_id}")
        print("\nMonitor progress in ComfyUI server logs...")
        print("This may take 3-5 minutes (14B is slower than 5B)")
        print("Watch for CUDA OOM errors!")
        return True
    else:
        print(f"[ERROR] Failed to queue")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    test_14b()
