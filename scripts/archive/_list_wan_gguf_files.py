from huggingface_hub import list_repo_files

repo = "bullerwins/Wan2.2-T2V-A14B-GGUF"
files = list_repo_files(repo)
q5 = [f for f in files if "Q5_K_M" in f and f.lower().endswith(".gguf")]

print("total", len(files))
print("q5_k_m", len(q5))
for f in sorted(q5):
    print(f)
