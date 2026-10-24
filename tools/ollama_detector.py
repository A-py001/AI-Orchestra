"""
Ollama Auto-Detection and Management Module for AI Orchestra
Detects running Ollama servers and locally installed models on disk.
"""
import os
import subprocess
import time
from typing import List, Tuple
import requests

DEFAULT_OLLAMA_URL = "http://localhost:11434"

def is_ollama_running(url: str = DEFAULT_OLLAMA_URL) -> bool:
    """Check if Ollama server is responding at the specified URL."""
    try:
        res = requests.get(f"{url}/api/tags", timeout=1.5)
        return res.status_code == 200
    except Exception:
        return False

def get_running_models(url: str = DEFAULT_OLLAMA_URL) -> List[str]:
    """Fetch all model names currently served by the running Ollama instance."""
    try:
        res = requests.get(f"{url}/api/tags", timeout=2.0)
        if res.status_code == 200:
            data = res.json()
            models = []
            for item in data.get("models", []):
                name = item.get("name", "")
                if name:
                    models.append(name)
            return sorted(models)
    except Exception:
        pass
    return []

def get_installed_models_from_disk() -> List[str]:
    """Scan the user's ~/.ollama/models directory for downloaded manifests."""
    home = os.path.expanduser("~")
    manifests_root = os.path.join(home, ".ollama", "models", "manifests")
    if not os.path.exists(manifests_root):
        return []

    models = set()
    try:
        for root, _, files in os.walk(manifests_root):
            for file in files:
                rel = os.path.relpath(os.path.join(root, file), manifests_root)
                parts = rel.replace("\\", "/").split("/")
                if len(parts) >= 3:
                    model_name = parts[-2]
                    tag = parts[-1]
                    models.add(f"{model_name}:{tag}")
    except Exception:
        pass

    return sorted(list(models))

def detect_ollama(url: str = DEFAULT_OLLAMA_URL) -> Tuple[bool, List[str]]:
    """
    Returns (is_active, available_models).
    If server is active, models are fetched via REST API.
    If server is inactive, models are detected directly from disk manifests.
    """
    active = is_ollama_running(url)
    if active:
        models = get_running_models(url)
        if not models:
            models = get_installed_models_from_disk()
        return True, models
    
    disk_models = get_installed_models_from_disk()
    return False, disk_models

def ensure_ollama_service(url: str = DEFAULT_OLLAMA_URL) -> bool:
    """
    Ensures that the Ollama server is running.
    If not running, attempts to start it in the background and waits up to 4 seconds.
    """
    if is_ollama_running(url):
        return True

    # Try starting via ollama serve or ollama.exe
    exe_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
        "ollama"
    ]
    for exe in exe_paths:
        try:
            subprocess.Popen(
                [exe, "serve"],
                creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Wait up to 3 seconds for server to initialize
            for _ in range(6):
                time.sleep(0.5)
                if is_ollama_running(url):
                    return True
        except Exception:
            pass

    return is_ollama_running(url)
