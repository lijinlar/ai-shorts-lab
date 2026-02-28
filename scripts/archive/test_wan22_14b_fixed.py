#!/usr/bin/env python3
"""
Test WAN 2.2 14B with CORRECT node and resolution
"""

import json
import requests
import time
import uuid

COMFYUI_URL = "http://127.0.0.1:8188"

def test_14b_fixed():
    """Test 14B with EmptyHunyuanLatentVideo node (correct for 14B)"""
    
    # Build corrected 14B workflow
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
                "text": "A golden retriever running happily through a sunlit meadow, tail wagging, slow motion, cinematic lighting, high quality, detailed fur, beautiful natural environment",
                "clip": ["1", 0]
            }
        },
        "6": {  # Negative Prompt
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality, static, ugly, deformed, watermark, text, distorted",
                "clip": ["1", 0]
            }
        },
        "7": {  # EmptyHunyuanLatentVideo (CORRECT node for 14B)
            "class_type": "EmptyHunyuanLatentVideo",
            "inputs": {
                "width": 704,      # Start smaller than optimal (1280x704)
                "height": 704,     # Square for 16GB safety
                "length": 41,      # ~1.7 sec @ 24fps (less than 57)
                "batch_size": 1
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
            "class_type": "KSamplerAdvanced",
            "inputs": {
                "add_noise": "enable",
                "noise_seed": int(time.time()),
                "steps": 20,
                "cfg": 3.5,
                "sampler_name": "euler",
                "scheduler": "simple",
                "start_at_step": 0,
                "end_at_step": 20,
                "return_with_leftover_noise": "enable",
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
            "class_type": "KSamplerAdvanced",
            "inputs": {
                "add_noise": "disable",
                "noise_seed": int(time.time()),
                "steps": 30,
                "cfg": 3.5,
                "sampler_name": "euler",
                "scheduler": "simple",
                "start_at_step": 20,
                "end_at_step": 30,
                "return_with_leftover_noise": "disable",
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
                "filename_prefix": "wan22_14b_704x704",
                "codec": "vp9",
                "fps": 24,
                "crf": 16,
                "images": ["12", 0]
            }
        }
    }
    
    print("=" * 60)
    print("WAN 2.2 14B - Fixed Resolution Test")
    print("=" * 60)
    print("\nCorrections:")
    print("- Using EmptyHunyuanLatentVideo (correct node for 14B)")
    print("- Resolution: 704x704 (conservative, can go 1280x704 later)")
    print("- Frames: 41 (~1.7 sec)")
    print("- Two-pass: High noise 20 steps -> Low noise 10 steps")
    print("\nPrompt: Golden retriever in meadow (enhanced)")
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
        print("\nThis will take 3-5 minutes...")
        print("Expected output: 704x704 video (not 256x256!)")
        return True
    else:
        print(f"[ERROR] Failed to queue")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    test_14b_fixed()
