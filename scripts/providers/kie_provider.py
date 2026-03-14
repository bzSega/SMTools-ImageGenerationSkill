import time
from datetime import datetime
from pathlib import Path

import requests

from providers.base_provider import BaseImageProvider
from config_manager import get_api_key, get_output_dir

# TODO: Replace with actual Kie.ai API endpoints once documentation is available
# See https://docs.kie.ai/ for API reference
TASK_SUBMIT_URL = "https://api.kie.ai/v1/tasks"  # TODO: verify endpoint
TASK_STATUS_URL = "https://api.kie.ai/v1/tasks/{task_id}"  # TODO: verify endpoint

DEFAULT_MODELS = [
    "flux-ai",
    "midjourney",
    "google-4o-image",
    "ghibli-ai",
]

# TODO: Map model names to Kie.ai API identifiers
MODEL_MAP = {
    "flux-ai": "flux-ai",  # TODO: verify API identifier
    "midjourney": "midjourney",  # TODO: verify API identifier
    "google-4o-image": "google-4o-image",  # TODO: verify API identifier
    "ghibli-ai": "ghibli-ai",  # TODO: verify API identifier
}


class KieProvider(BaseImageProvider):
    name = "kie"

    def __init__(self, config: dict):
        self.config = config
        self.provider_config = config.get("providers", {}).get("kie", {})
        self.default_model = self.provider_config.get(
            "default_model", "google-4o-image"
        )
        self.poll_interval = self.provider_config.get("poll_interval", 5)
        self.max_wait = self.provider_config.get("max_wait", 300)

    def validate_config(self, config: dict) -> bool:
        try:
            get_api_key("kie")
            return True
        except EnvironmentError:
            return False

    def list_models(self) -> list:
        return DEFAULT_MODELS

    def generate(self, prompt: str, model: str = None, output_path: str = None) -> dict:
        api_key = get_api_key("kie")
        model = model or self.default_model
        api_model = MODEL_MAP.get(model, model)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Step 1: Submit task
        # TODO: Adjust payload format per Kie.ai API docs
        payload = {
            "model": api_model,
            "prompt": prompt,
        }

        response = requests.post(
            TASK_SUBMIT_URL, headers=headers, json=payload, timeout=30
        )
        response.raise_for_status()

        task_data = response.json()
        task_id = task_data.get("task_id")  # TODO: verify response field name

        if not task_id:
            return {
                "status": "error",
                "error": "No task_id in response",
                "provider": self.name,
                "model": model,
            }

        # Step 2: Poll for completion
        result_url = self._poll_until_done(task_id, headers)

        if result_url is None:
            return {
                "status": "error",
                "error": f"Task {task_id} timed out after {self.max_wait}s",
                "provider": self.name,
                "model": model,
            }

        # Step 3: Download and save image
        if output_path is None:
            output_dir = get_output_dir(self.config)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"img_{timestamp}.png"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        img_response = requests.get(result_url, timeout=60)
        img_response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(img_response.content)

        return {
            "status": "ok",
            "image_path": str(output_path.resolve()),
            "model": model,
            "provider": self.name,
            "metadata": {
                "task_id": task_id,
                "size_bytes": len(img_response.content),
            },
        }

    def _poll_until_done(self, task_id: str, headers: dict) -> str:
        """Poll task status with exponential backoff until done or timeout."""
        elapsed = 0
        interval = self.poll_interval

        while elapsed < self.max_wait:
            time.sleep(interval)
            elapsed += interval

            url = TASK_STATUS_URL.format(task_id=task_id)
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()

            data = resp.json()
            status = data.get("status")  # TODO: verify field name

            if status == "completed":  # TODO: verify status value
                # TODO: verify how result URL is returned
                return data.get("result", {}).get("url")

            if status in ("failed", "error"):  # TODO: verify error statuses
                return None

            # Exponential backoff, capped at 30s
            interval = min(interval * 1.5, 30)

        return None
