# Last Edit: 11/06/2026, Thursday (Brisbane Time)
# Claude (Anthropic) vision client for floor plan analysis (PRIMARY)
# Migrated OpenAI gpt-5.4 → Claude via shared/claude_vision.py (2026-06-11):
# OpenAI quota exhaustion (429 insufficient_quota) had stalled step 106 nightly.

"""
Claude vision client module for floor plan analysis.
Class name OpenAIFloorPlanClient is kept as an alias so
ollama_floorplan_client.py needs no import changes.
"""
import json
import os
import sys
import time
import base64

import requests

from logger import logger
from prompts_floorplan import get_floor_plan_basic_prompt

# shared/claude_vision.py lives in the orchestrator repo
_ORCH = "/home/fields/Fields_Orchestrator"
if _ORCH not in sys.path:
    sys.path.insert(0, _ORCH)
if not os.environ.get("ANTHROPIC_API_KEY"):
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_ORCH, ".env"), override=False)

from shared.claude_vision import vision_text, MODEL_ANALYZE  # noqa: E402
from shared.blob_storage import to_live_url as _to_live_url  # noqa: E402

CLAUDE_FLOORPLAN_MODEL = os.environ.get("FLOORPLAN_CLAUDE_MODEL", MODEL_ANALYZE)


class ClaudeFloorPlanClient:
    """Client for analyzing floor plans using Claude vision."""

    def __init__(self):
        """Initialize Claude floor plan client."""
        self.model = CLAUDE_FLOORPLAN_MODEL

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        logger.info(f"Initialized Claude floor plan client with model: {self.model}")

    def _download_and_encode_image(self, image_url):
        """
        Download image from URL, normalise to PNG, and encode to base64.

        Floor plans are line drawings — PNG keeps the thin walls/dimension text
        crisp where JPEG artefacts can blur them.

        Args:
            image_url: URL of the image to download

        Returns:
            Base64 encoded image string (PNG format), no data-URI prefix
        """
        try:
            from PIL import Image
            from io import BytesIO

            # Stored URLs may still point at the retired Azure account (403 "account
            # is disabled"). Same path, live host — rewrite before fetching.
            image_url = _to_live_url(image_url)

            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Open image with PIL to handle format conversion
            img = Image.open(BytesIO(response.content))

            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Bound size for Anthropic's 5MB per-image cap; 2200px keeps
            # dimension text on plans comfortably legible.
            img.thumbnail((2200, 2200))

            png_buffer = BytesIO()
            img.save(png_buffer, format='PNG')
            png_data = png_buffer.getvalue()

            image_data = base64.b64encode(png_data).decode('utf-8')

            logger.info(f"Converted image to PNG format ({len(png_data)} bytes)")
            return image_data

        except Exception as e:
            logger.error(f"Failed to download/encode image {image_url}: {e}")
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

    def analyze_floor_plan(self, floor_plan_url, address):
        """
        Analyze a single floor plan image using Claude vision.

        Args:
            floor_plan_url: URL of the floor plan image
            address: Property address for logging

        Returns:
            Parsed JSON response with floor plan data
        """
        try:
            start_time = time.time()

            # Download and encode floor plan image
            logger.info(f"[CLAUDE] Downloading floor plan image for {address}...")
            encoded_image = self._download_and_encode_image(floor_plan_url)

            if not encoded_image:
                raise ValueError("Failed to download and encode floor plan image")

            logger.info(f"[CLAUDE] Successfully encoded floor plan image")

            # Prepare the prompt
            prompt = get_floor_plan_basic_prompt()

            # Call Claude
            logger.info(f"[CLAUDE] Sending floor plan to Claude...")
            content = vision_text(
                prompt,
                ("image/png", encoded_image),
                model=self.model,
                max_tokens=8000,
            )

            elapsed_time = time.time() - start_time
            logger.info(f"[CLAUDE] Floor plan analysis complete for {address} ({elapsed_time:.1f}s)")

            # Log response for debugging
            if not content or len(content.strip()) == 0:
                logger.error(f"[CLAUDE] Empty response from Claude for {address}")
                raise ValueError("Empty response from Claude")

            logger.debug(f"Response length: {len(content)} characters")

            # Parse JSON response
            result = self._parse_json(content)
            if result is None:
                logger.error(f"[CLAUDE] Failed to parse Claude response as JSON")
                logger.error(f"Response content: {content[:1000]}")
                raise ValueError("Unparseable JSON response from Claude")
            logger.info("[CLAUDE] JSON parsed successfully")

            # Add metadata to indicate the engine used
            result["analysis_engine"] = "claude"
            result["model_used"] = self.model

            return result

        except Exception as e:
            logger.error(f"[CLAUDE] Claude API error for {address}: {e}")
            raise

    def analyze_property_floor_plans(self, floor_plan_urls, address):
        """
        Analyze floor plan images for a property using Claude.

        Args:
            floor_plan_urls: List of floor plan image URLs
            address: Property address for logging

        Returns:
            Dictionary with floor plan analysis results
        """
        try:
            if not floor_plan_urls:
                logger.warning(f"[CLAUDE] No floor plans provided for {address}")
                return {
                    "has_floor_plan": False,
                    "floor_plans_analyzed": 0,
                    "message": "No floor plan images provided"
                }

            # Analyze each floor plan
            floor_plan_analyses = []

            for idx, floor_plan_url in enumerate(floor_plan_urls):
                logger.info(f"[CLAUDE] Analyzing floor plan {idx + 1}/{len(floor_plan_urls)} for {address}")

                analysis = self.analyze_floor_plan(floor_plan_url, address)

                # Add metadata
                analysis["floor_plan_url"] = floor_plan_url
                analysis["floor_plan_index"] = idx

                floor_plan_analyses.append(analysis)

            # Combine results
            result = {
                "has_floor_plan": True,
                "floor_plans_analyzed": len(floor_plan_analyses),
                "floor_plan_data": floor_plan_analyses[0] if len(floor_plan_analyses) == 1 else floor_plan_analyses,
                "model_used": self.model,
                "analysis_engine": "claude",
                "analyzed_at": time.time()
            }

            logger.info(f"[CLAUDE] Successfully analyzed {len(floor_plan_analyses)} floor plan(s) for {address}")

            return result

        except Exception as e:
            logger.error(f"[CLAUDE] Error analyzing floor plans for {address}: {e}")
            return {
                "has_floor_plan": False,
                "floor_plans_analyzed": 0,
                "error": str(e),
                "message": "Floor plan analysis failed (Claude)"
            }


# Backwards-compatible alias — ollama_floorplan_client.py imports this name.
OpenAIFloorPlanClient = ClaudeFloorPlanClient
