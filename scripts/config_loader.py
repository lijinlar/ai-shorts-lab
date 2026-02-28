"""
config_loader.py — Load ai-shorts-lab user configuration from config.yaml

Usage in any script:
    from config_loader import get_wangp_dir, get_oauth_credentials

The config.yaml file must exist in the project root (one level above scripts/).
Copy config.example.yaml → config.yaml and fill in your paths.
"""

from pathlib import Path
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _ROOT / "config.yaml"
_EXAMPLE_PATH = _ROOT / "config.example.yaml"

_config = None


def _load() -> dict:
    global _config
    if _config is not None:
        return _config
    if not _CONFIG_PATH.exists():
        raise SystemExit(
            f"\n[ai-shorts-lab] Missing config.yaml\n"
            f"  Copy config.example.yaml → config.yaml and fill in your paths:\n"
            f"  {_CONFIG_PATH}\n"
        )
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        _config = yaml.safe_load(f)
    return _config


def get_wangp_dir() -> Path:
    """Returns the WanGP installation directory as a Path."""
    cfg = _load()
    raw = cfg.get("wangp", {}).get("dir", "")
    if not raw or raw == "C:/path/to/Wan2GP":
        raise SystemExit(
            "[ai-shorts-lab] wangp.dir is not configured in config.yaml\n"
            "  Set it to the path of your WanGP installation."
        )
    p = Path(raw)
    if not p.exists():
        raise SystemExit(
            f"[ai-shorts-lab] WanGP directory not found: {p}\n"
            "  Check wangp.dir in config.yaml"
        )
    return p


def get_oauth_credentials() -> Path:
    """Returns the YouTube OAuth credentials JSON file as a Path."""
    cfg = _load()
    raw = cfg.get("youtube", {}).get("oauth_credentials", "")
    if not raw or raw == "C:/path/to/youtube.oauth.json":
        raise SystemExit(
            "[ai-shorts-lab] youtube.oauth_credentials is not configured in config.yaml\n"
            "  Download your OAuth2 client JSON from Google Cloud Console and set the path."
        )
    p = Path(raw)
    if not p.exists():
        raise SystemExit(
            f"[ai-shorts-lab] OAuth credentials file not found: {p}\n"
            "  Check youtube.oauth_credentials in config.yaml"
        )
    return p


def get_project_root() -> Path:
    """Returns the project root directory."""
    return _ROOT
