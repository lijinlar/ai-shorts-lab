from huggingface_hub import list_repo_files

repo = "bullerwins/Wan2.2-T2V-A14B-GGUF"
files = list_repo_files(repo)
for f in sorted(files):
    if f.lower().endswith((".json", ".png", ".txt", ".workflow", ".zip")):
        print(f)
