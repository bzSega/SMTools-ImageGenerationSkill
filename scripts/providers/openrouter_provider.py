import base64
import requests

from datetime import datetime
from pathlib import Path

from providers.base_provider import BaseImageProvider
from config_manager import get_api_key, get_output_dir

# Standard OpenAI-compatible image generation endpoint — works with all
# image generation models on OpenRouter (DALL-E, Stable Diffusion, Imagen, etc.)
IMAGES_URL = "https://openrouter.ai/api/v1/images/generations"

DEFAULT_MODELS = [
    "google/gemini-3.1-flash-image-preview",
    "openai/gpt-image-1",
    "google/imagen-4",
    "stabilityai/stable-diffusion-3",
]


class OpenRouterProvider(BaseImageProvider):
    name = "openrouter"

    def __init__(self, config: dict):
        self.config = config
        self.provider_config = config.get("providers", {}).get("openrouter", {})
        self.default_model = self.provider_config.get(
            "default_model", "google/gemini-3.1-flash-image-preview"
        )

    def validate_config(self, config: dict) -> bool:
        try:
            get_api_key("openrouter")
            return True
        except EnvironmentError:
            return False

    def list_models(self) -> list:
        return DEFAULT_MODELS

    def generate(self, prompt: str, model: str = None, output_path: str = None) -> dict:
        api_key = get_api_key("openrouter")
        model = model or self.default_model

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "response_format": "b64_json",
        }

        response = requests.post(IMAGES_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        items = data.get("data", [])

        if not items:
            return {
                "status": "error",
                "error": "No image in API response",
                "provider": self.name,
                "model": model,
            }

        item = items[0]
        b64 = item.get("b64_json")

        # Some models return a URL instead of base64
        if not b64 and item.get("url"):
            img_resp = requests.get(item["url"], timeout=60)
            img_resp.raise_for_status()
            image_bytes = img_resp.content
        elif b64:
            image_bytes = base64.b64decode(b64)
        else:
            return {
                "status": "error",
                "error": "Response contains neither b64_json nor url",
                "provider": self.name,
                "model": model,
            }

        if output_path is None:
            output_dir = get_output_dir(self.config)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"img_{timestamp}.png"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        return {
            "status": "ok",
            "image_path": str(output_path.resolve()),
            "model": model,
            "provider": self.name,
            "metadata": {"size_bytes": len(image_bytes)},
        }
