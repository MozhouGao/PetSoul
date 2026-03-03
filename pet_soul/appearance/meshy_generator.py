"""
Meshy.ai 3D Generator
Sends pet images to the Meshy image-to-3D API and downloads the resulting GLB model.
"""

import base64
import logging
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import requests
from PIL import Image

logger = logging.getLogger(__name__)

MESHY_API_BASE = "https://api.meshy.ai/openapi/v1"


class MeshyGenerator:
    """Generates 3D models via the Meshy.ai image-to-3D API.

    Requires the MESHY_API_KEY environment variable to be set.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        ai_model: str = "meshy-6",
        target_polycount: int = 30000,
        topology: str = "triangle",
        enable_pbr: bool = True,
        poll_interval: float = 5.0,
        timeout: float = 300.0,
    ):
        self.api_key = api_key or os.environ.get("MESHY_API_KEY", "")
        self.ai_model = ai_model
        self.target_polycount = target_polycount
        self.topology = topology
        self.enable_pbr = enable_pbr
        self.poll_interval = poll_interval
        self.timeout = timeout

        if not self.api_key:
            logger.warning("MESHY_API_KEY not set — MeshyGenerator will not work")

    # ------------------------------------------------------------------
    # Public interface (compatible with pipeline expectations)
    # ------------------------------------------------------------------

    def generate(self, image: np.ndarray, output_format: str = "glb",
                 texture_prompt: Optional[str] = None,
                 texture_image: Optional[np.ndarray] = None) -> Dict:
        """Submit an image to Meshy and return the result.

        Args:
            image: Cropped pet image as a numpy RGB array.
            output_format: Desired format (glb, fbx, obj, usdz).
            texture_prompt: Optional text hint for texturing.

        Returns:
            Dict with 'success', 'model_url', 'task_id', and optionally
            'model_data' (raw bytes of the downloaded model).
        """
        try:
            if not self.api_key:
                return {"success": False, "error": "MESHY_API_KEY not configured"}

            # Encode image as base64 data URI
            image_data_uri = self._image_to_data_uri(image)

            # Encode texture reference image if provided
            texture_image_uri = None
            if texture_image is not None:
                texture_image_uri = self._image_to_data_uri(texture_image)

            # Step 1: Create task
            task_id = self._create_task(image_data_uri, texture_prompt,
                                        texture_image_uri)
            if not task_id:
                return {"success": False, "error": "Failed to create Meshy task"}

            logger.info("Meshy task created: %s", task_id)

            # Step 2: Poll until done
            task = self._poll_task(task_id)
            if task is None:
                return {"success": False, "error": "Meshy task timed out or failed",
                        "task_id": task_id}

            status = task.get("status")
            if status != "SUCCEEDED":
                return {"success": False,
                        "error": f"Meshy task ended with status: {status}",
                        "task_id": task_id}

            # Step 3: Get model URL
            model_urls = task.get("model_urls", {})
            model_url = model_urls.get(output_format) or model_urls.get("glb")
            if not model_url:
                return {"success": False,
                        "error": "No model URL in Meshy response",
                        "task_id": task_id}

            # Step 4: Download model bytes
            model_data = self._download(model_url)
            if model_data is None:
                return {"success": False,
                        "error": "Failed to download model from Meshy",
                        "task_id": task_id, "model_url": model_url}

            logger.info("Meshy model downloaded: %d bytes", len(model_data))

            return {
                "success": True,
                "task_id": task_id,
                "model_url": model_url,
                "model_data": model_data,
                "thumbnail_url": task.get("thumbnail_url"),
            }

        except Exception as e:
            logger.exception("MeshyGenerator.generate failed")
            return {"success": False, "error": str(e)}

    def save_mesh(self, mesh_data: Dict, output_path: str,
                  output_format: str = "glb") -> bool:
        """Write downloaded model bytes to a file."""
        try:
            data = mesh_data.get("model_data")
            if not data:
                logger.error("No model_data to save")
                return False

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(data)

            logger.info("Model saved to %s (%d bytes)", output_path, len(data))
            return True

        except Exception as e:
            logger.exception("Error saving Meshy model")
            return False

    def is_ready(self) -> bool:
        """Check if the generator is configured and reachable."""
        return bool(self.api_key)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _image_to_data_uri(image: np.ndarray) -> str:
        """Convert a numpy RGB image to a base64 data URI."""
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        pil = Image.fromarray(image)
        buf = BytesIO()
        pil.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    def _create_task(self, image_data_uri: str,
                     texture_prompt: Optional[str] = None,
                     texture_image_uri: Optional[str] = None) -> Optional[str]:
        """POST to Meshy image-to-3d endpoint, return task_id."""
        payload = {
            "image_url": image_data_uri,
            "ai_model": self.ai_model,
            "topology": self.topology,
            "target_polycount": self.target_polycount,
            "should_texture": True,
            "enable_pbr": self.enable_pbr,
        }
        if texture_prompt:
            payload["texture_prompt"] = texture_prompt[:600]
        if texture_image_uri:
            payload["texture_image_url"] = texture_image_uri

        resp = requests.post(
            f"{MESHY_API_BASE}/image-to-3d",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )

        if resp.status_code not in (200, 201, 202):
            logger.error("Meshy create task failed: %s %s", resp.status_code, resp.text)
            return None

        data = resp.json()
        return data.get("result")

    def _poll_task(self, task_id: str) -> Optional[Dict]:
        """Poll Meshy until the task completes or times out."""
        url = f"{MESHY_API_BASE}/image-to-3d/{task_id}"
        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            resp = requests.get(url, headers=self._headers(), timeout=30)
            if resp.status_code != 200:
                logger.warning("Meshy poll error: %s", resp.status_code)
                time.sleep(self.poll_interval)
                continue

            task = resp.json()
            status = task.get("status", "UNKNOWN")
            progress = task.get("progress", 0)
            logger.info("Meshy task %s: status=%s progress=%d%%",
                        task_id, status, progress)

            if status in ("SUCCEEDED", "FAILED", "CANCELED"):
                return task

            time.sleep(self.poll_interval)

        logger.error("Meshy task %s timed out after %.0fs", task_id, self.timeout)
        return None

    @staticmethod
    def _download(url: str) -> Optional[bytes]:
        """Download a file from a signed URL."""
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                return resp.content
            logger.error("Download failed: %s", resp.status_code)
            return None
        except Exception as e:
            logger.error("Download error: %s", e)
            return None
