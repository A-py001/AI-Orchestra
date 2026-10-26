"""
9Router Auto-Detection and Management Module for AI Orchestra
Detects running 9Router local AI gateway instances (http://localhost:20128)
and fetches available models, combos, and provider aliases.
"""
import requests
from typing import List, Tuple

DEFAULT_9ROUTER_URL = "http://localhost:20128"


def is_9router_running(url: str = DEFAULT_9ROUTER_URL) -> bool:
    """Check if 9Router server is responding at the specified URL with a strict short timeout."""
    try:
        # Check either /health or /v1/models
        res = requests.get(f"{url}/v1/models", timeout=0.8)
        return res.status_code == 200
    except Exception:
        return False


def get_9router_models(url: str = DEFAULT_9ROUTER_URL) -> List[str]:
    """Fetch model IDs and combo names currently served by 9Router."""
    try:
        res = requests.get(f"{url}/v1/models", timeout=1.0)
        if res.status_code == 200:
            data = res.json()
            models = []
            # OpenAI standard models list: {"data": [{"id": "..."}, ...]}
            for item in data.get("data", []):
                m_id = item.get("id", "")
                if m_id:
                    models.append(m_id)
            return sorted(models)
    except Exception:
        pass
    return []


def detect_9router(url: str = DEFAULT_9ROUTER_URL) -> Tuple[bool, List[str]]:
    """
    Returns (is_active, available_models).
    Fast check designed for lazy startup without blocking terminal rendering.
    """
    active = is_9router_running(url)
    if active:
        models = get_9router_models(url)
        return True, models
    return False, []
