#!/usr/bin/env python3
"""Quick WAN2.2 test - generate a dog video for comparison"""

import torch
from diffusers import WanPipeline
from pathlib import Path
import time

def main():
    output_dir = Path(__file__).resolve().parents[1] / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    print("Loading WAN2.2 5B pipeline...")
    
    # Use local models
    model_path = "C:/Users/lijin/Projects/ComfyUI/models/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"
    
    # Check if diffusers supports WAN directly, otherwise use transformers approach
    try:
        from huggingface_hub import hf_hub_download
        from diffusers import DiffusionPipeline
        
        # Try loading from HuggingFace (will use cache if available)
        pipe = DiffusionPipeline.from_pretrained(
            "Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
            torch_dtype=torch.float16,
            variant="fp16"
        )
        pipe = pipe.to("cuda")
        
        # Dog emotional prompt matching YouTube content
        prompt = "Golden retriever dog running joyfully through sunny meadow, tail wagging happily, slow motion, emotional moment, cinematic lighting, high quality, detailed fur"
        
        negative_prompt = "blurry, low quality, static, distorted, ugly"
        
        print(f"\nPrompt: {prompt}")
        print("\nGenerating video (this will take 2-3 minutes)...")
        
        start = time.time()
        
        output = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=25,  # ~1 second @ 25fps
            height=512,
            width=512,
            num_inference_steps=30,
            guidance_scale=6.0
        ).frames[0]
        
        duration = time.time() - start
        
        # Save video
        output_path = output_dir / f"wan22_test_{int(time.time())}.mp4"
        
        # Convert frames to video
        import cv2
        import numpy as np
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, 25.0, (512, 512))
        
        for frame in output:
            frame_np = np.array(frame)
            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
        
        out.release()
        
        print(f"\n✅ Video generated in {duration:.1f}s")
        print(f"📁 Saved to: {output_path}")
        print(f"📊 Resolution: 512x512, 25 frames")
        
        return str(output_path)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nWAN2.2 requires ComfyUI workflow for now.")
        print("Starting ComfyUI server is recommended for full testing.")
        return None

if __name__ == "__main__":
    main()
