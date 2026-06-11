# Last Edit: 11/06/2026, Thursday (Brisbane Time)
# Claude (Anthropic) vision client for property photo analysis.
# Migrated OpenAI gpt-5.4 → Claude via shared/claude_vision.py (2026-06-11):
# OpenAI quota exhaustion (429 insufficient_quota) had stalled step 105 nightly.
"""
Claude vision client for property photo analysis.
Maintains the same interface as the former OllamaClientSingleImage /
OpenAI implementation so that worker_multi.py requires no changes.
"""
import json
import os
import sys
import time
import base64
from io import BytesIO

import requests
from PIL import Image

from config import MAX_RETRIES, RETRY_DELAY  # noqa: F401  (kept for interface parity)
from logger import logger

# shared/claude_vision.py lives in the orchestrator repo
_ORCH = "/home/fields/Fields_Orchestrator"
if _ORCH not in sys.path:
    sys.path.insert(0, _ORCH)
if not os.environ.get("ANTHROPIC_API_KEY"):
    # Manual runs from this dir don't inherit the orchestrator env
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_ORCH, ".env"), override=False)

from shared.claude_vision import vision_text, MODEL_ANALYZE  # noqa: E402

CLAUDE_PHOTO_MODEL = os.environ.get("PHOTO_ANALYSIS_CLAUDE_MODEL", MODEL_ANALYZE)


class OllamaClientSingleImage:
    """Photo analysis client using Claude vision (Anthropic API)."""

    def __init__(self):
        self.model = CLAUDE_PHOTO_MODEL

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        logger.info(f"Initialized Claude photo analysis client with model: {self.model}")

    def _download_and_encode_image(self, image_url):
        """Download image, normalise to JPEG, return base64 (no data-URI prefix)."""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.thumbnail((1568, 1568))  # Anthropic per-image cap is 5MB / ~1568px optimal
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=90)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to download image {image_url}: {e}")
            return None

    @staticmethod
    def _parse_json(content):
        """Parse model output as JSON, tolerating surrounding prose/fences."""
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            pass
        if not content:
            return None
        first, last = content.find("{"), content.rfind("}")
        if first != -1 and last > first:
            try:
                return json.loads(content[first:last + 1])
            except json.JSONDecodeError:
                return None
        return None

    def _analyze_single_image(self, encoded_image, image_index):
        """Analyze a single image with Claude vision."""
        prompt = f"""Analyze this property image (image #{image_index}).

Provide a JSON response with:
{{
  "image_type": "exterior/interior/kitchen/bathroom/bedroom/living_room/outdoor/pool/garage/floor_plan/other",
  "description": "brief description of what the image shows",
  "usefulness_score": 1-10,
  "quality_score": 1-10,
  "marketing_value": "high/medium/low",
  "features_visible": ["list", "of", "visible", "features"]
}}

Return ONLY valid JSON, no other text."""

        try:
            content = vision_text(
                prompt,
                ("image/jpeg", encoded_image),
                model=self.model,
                max_tokens=1500,
            )
            if not content:
                raise ValueError("Empty response from Claude")
            result = self._parse_json(content)
            if result is None:
                raise ValueError(f"Unparseable JSON response: {content[:200]}")
            return result
        except Exception as e:
            logger.error(f"Failed to analyze image {image_index}: {e}")
            return None

    def analyze_property_images(self, image_urls, address, max_images=5):
        """Analyze property images and return aggregated results."""
        images_to_use = image_urls[:max_images]
        logger.info(f"Analyzing {len(images_to_use)} images for {address}")

        start_time = time.time()
        image_analyses = []

        for idx, url in enumerate(images_to_use):
            logger.info(f"Processing image {idx + 1}/{len(images_to_use)}...")
            encoded = self._download_and_encode_image(url)
            if not encoded:
                logger.warning(f"Skipping image {idx} - download failed")
                continue
            analysis = self._analyze_single_image(encoded, idx)
            if analysis:
                analysis["image_index"] = idx
                analysis["url"] = url
                image_analyses.append(analysis)
                logger.info(
                    f"Image {idx}: {analysis.get('image_type', 'unknown')} - score {analysis.get('usefulness_score', 0)}/10"
                )

        elapsed = time.time() - start_time
        logger.info(f"Analyzed {len(image_analyses)} images in {elapsed:.1f}s")

        return {
            "image_analysis": image_analyses,
            "metadata": {
                "total_images_analyzed": len(image_analyses),
                "processing_time_seconds": elapsed,
            },
        }

    def extract_image_analysis(self, analysis_result, image_urls):
        """Extract and sort image analysis by usefulness score."""
        image_analysis = analysis_result.get("image_analysis", [])
        image_analysis.sort(key=lambda x: x.get("usefulness_score", 0), reverse=True)
        logger.info(f"Extracted {len(image_analysis)} image analyses")
        return image_analysis

    def extract_property_data(self, analysis_result):
        """Extract aggregated property data from image analyses."""
        image_analyses = analysis_result.get("image_analysis", [])

        all_features = []
        for img in image_analyses:
            all_features.extend(img.get("features_visible", []))

        return {
            "structural": {},
            "exterior": {},
            "interior": {},
            "renovation": {},
            "outdoor": {},
            "layout": {},
            "overall": {"unique_features": list(set(all_features))},
            "metadata": {
                "model_used": self.model,
                "extracted_at": time.time(),
                "analysis_engine": "claude",
                "analysis_method": "single_image_aggregation",
                "total_images_analyzed": len(image_analyses),
            },
        }
