#!/usr/bin/env python3
"""
Test WAN 2.2 video generation via ComfyUI API
"""

import json
import requests
import time
import uuid
import os

COMFYUI_URL = "http://127.0.0.1:8188"

def queue_prompt(workflow):
    """Send workflow to ComfyUI queue"""
    p = {"prompt": workflow, "client_id": str(uuid.uuid4())}
    data = json.dumps(p).encode('utf-8')
    req = requests.post(f"{COMFYUI_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    print(f"API Response Status: {req.status_code}")
    print(f"API Response: {req.text[:200]}")
    try:
        return json.loads(req.text)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print(f"Full response: {req.text}")
        return {"error": "Invalid JSON response from ComfyUI"}

def get_history(prompt_id):
    """Get generation history"""
    resp = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
    return json.loads(resp.text)

def test_wan22_video_generation():
    """Test video generation with dog-themed prompt"""
    
    print("=" * 60)
    print("Testing WAN 2.2 5B Text-to-Video Generation")
    print("=" * 60)
    
    # Load workflow
    workflow_path = r"C:\Users\lijin\Projects\ComfyUI\workflows\wan22_text_to_video_5B.json"
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow_data = json.load(f)
    
    # Convert workflow format: array of nodes -> dict of nodes
    workflow = {}
    for node in workflow_data["nodes"]:
        node_id = str(node["id"])
        workflow[node_id] = {
            "class_type": node["type"],
            "inputs": {}
        }
        
        # Add widgets as inputs
        if "widgets_values" in node and node["widgets_values"]:
            # Find widget names from node type (this is simplified)
            if node["type"] == "CLIPTextEncode":
                workflow[node_id]["inputs"]["text"] = node["widgets_values"][0]
            elif node["type"] == "Wan22ImageToVideoLatent":
                workflow[node_id]["inputs"]["width"] = node["widgets_values"][0]
                workflow[node_id]["inputs"]["height"] = node["widgets_values"][1]
                workflow[node_id]["inputs"]["frames"] = node["widgets_values"][2]
                workflow[node_id]["inputs"]["batch_size"] = node["widgets_values"][3]
            elif node["type"] == "VAELoader":
                workflow[node_id]["inputs"]["vae_name"] = node["widgets_values"][0]
            elif node["type"] == "CLIPLoader":
                workflow[node_id]["inputs"]["clip_name"] = node["widgets_values"][0]
                workflow[node_id]["inputs"]["type"] = node["widgets_values"][1]
            elif node["type"] == "UNETLoader":
                workflow[node_id]["inputs"]["unet_name"] = node["widgets_values"][0]
                workflow[node_id]["inputs"]["weight_dtype"] = node["widgets_values"][1]
            elif node["type"] == "ModelSamplingSD3":
                workflow[node_id]["inputs"]["shift"] = node["widgets_values"][0]
            elif node["type"] == "KSampler":
                workflow[node_id]["inputs"]["seed"] = node["widgets_values"][0]
                workflow[node_id]["inputs"]["steps"] = node["widgets_values"][2]
                workflow[node_id]["inputs"]["cfg"] = node["widgets_values"][3]
                workflow[node_id]["inputs"]["sampler_name"] = node["widgets_values"][4]
                workflow[node_id]["inputs"]["scheduler"] = node["widgets_values"][5]
                workflow[node_id]["inputs"]["denoise"] = node["widgets_values"][6]
        
        # Add inputs from connections
        if "inputs" in node:
            for inp in node["inputs"]:
                if "link" in inp and inp["link"] is not None:
                    # Find source node
                    for link in workflow_data["links"]:
                        if link[0] == inp["link"]:
                            source_node_id = str(link[1])
                            source_output_idx = link[2]
                            workflow[node_id]["inputs"][inp["name"]] = [source_node_id, source_output_idx]
                            break
    
    # Modify prompt (node 6 is the positive prompt)
    test_prompt = "A golden retriever running happily through a sunlit meadow, tail wagging, slow motion, cinematic, beautiful lighting"
    workflow["6"]["inputs"]["text"] = test_prompt
    
    # Reduce resolution and length for faster test (node 55)
    workflow["55"]["inputs"]["width"] = 512
    workflow["55"]["inputs"]["height"] = 512
    workflow["55"]["inputs"]["frames"] = 25
    
    print(f"\nTest Prompt: {test_prompt}")
    print(f"Resolution: 512x512, 25 frames (~1 second @ 24fps)")
    print("\nQueuing generation...")
    
    # Queue the prompt
    response = queue_prompt(workflow)
    
    if "error" in response:
        print(f"\n[ERROR] {response['error']}")
        print(f"Details: {response.get('node_errors', {})}")
        return False
    
    prompt_id = response["prompt_id"]
    print(f"Prompt ID: {prompt_id}")
    print("\nGenerating video... (this may take 2-5 minutes)")
    print("Monitor VRAM usage in Task Manager -> GPU")
    
    # Poll for completion
    start_time = time.time()
    while True:
        history = get_history(prompt_id)
        
        if prompt_id in history:
            elapsed = time.time() - start_time
            print(f"\n[SUCCESS] Generation completed in {elapsed:.1f} seconds!")
            
            # Check outputs
            outputs = history[prompt_id].get("outputs", {})
            print("\nOutputs:")
            for node_id, output in outputs.items():
                if "images" in output:
                    for img in output["images"]:
                        print(f"  - {img['type']}: {img['filename']}")
                elif "videos" in output:
                    for vid in output["videos"]:
                        print(f"  - Video: {vid['filename']}")
            
            return True
        
        time.sleep(2)
        print(".", end="", flush=True)
        
        # Timeout after 10 minutes
        if time.time() - start_time > 600:
            print("\n[TIMEOUT] Generation took too long")
            return False

if __name__ == "__main__":
    try:
        success = test_wan22_video_generation()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        exit(1)
