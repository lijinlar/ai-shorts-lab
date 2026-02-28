#!/usr/bin/env python3
"""
Test WAN 2.2 5B model for video generation
Standalone test - does NOT replace current pipeline
"""

import sys
import os

# Add ComfyUI to path
comfyui_path = r"C:\Users\lijin\Projects\ComfyUI"
sys.path.insert(0, comfyui_path)

def test_wan22_basic():
    """Basic test to verify WAN 2.2 models are loaded correctly"""
    print("Testing WAN 2.2 5B model setup...")
    print("=" * 60)
    
    # Check model files exist
    models = {
        "Diffusion Model": os.path.join(comfyui_path, "models/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"),
        "Text Encoder": os.path.join(comfyui_path, "models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"),
        "VAE": os.path.join(comfyui_path, "models/vae/wan2.2_vae.safetensors"),
        "Workflow JSON": os.path.join(comfyui_path, "workflows/wan22_text_to_video_5B.json")
    }
    
    all_exist = True
    for name, path in models.items():
        exists = os.path.exists(path)
        status = "[OK]" if exists else "[MISSING]"
        size = f"{os.path.getsize(path) / 1024**3:.2f}GB" if exists else "N/A"
        print(f"{status} {name}: {size}")
        if not exists:
            all_exist = False
    
    print("=" * 60)
    
    if not all_exist:
        print("[ERROR] Some required files are missing!")
        return False
    
    print("[SUCCESS] All WAN 2.2 model files present!")
    print("\nNext steps:")
    print("1. Start ComfyUI server: python main.py --listen 127.0.0.1 --port 8188")
    print("2. Run actual generation test with sample prompt")
    print("3. Integrate into batch_generate_upload_series.py as --pipeline=wan22 option")
    
    return True

if __name__ == "__main__":
    success = test_wan22_basic()
    sys.exit(0 if success else 1)
