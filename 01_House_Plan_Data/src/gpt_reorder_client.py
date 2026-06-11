"""
Claude client for photo reordering system.

Migrated OpenAI → Claude (2026-06-11) via shared/claude_vision.py after OpenAI
quota exhaustion stalled step 105. The reorder task is text-only (it works from
per-image descriptions produced by the photo analysis pass, not the images
themselves), so the migration is a straight chat-call swap. Class name kept as
GPTReorderClient so run_photo_reorder.py needs no changes.
"""
import json
import os
import sys
import time
from pathlib import Path
from logger import logger
from prompts_reorder import get_photo_reorder_prompt

# shared/claude_vision.py lives in the orchestrator repo
_ORCH = "/home/fields/Fields_Orchestrator"
if _ORCH not in sys.path:
    sys.path.insert(0, _ORCH)
if not os.environ.get("ANTHROPIC_API_KEY"):
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_ORCH, ".env"), override=False)

from shared.claude_vision import vision_text, MODEL_ANALYZE  # noqa: E402

REORDER_SYSTEM_PROMPT = (
    "You are a real estate photography expert specializing in "
    "creating optimal virtual property tours."
)


class GPTReorderClient:
    """Client for creating photo tour orders via the Claude API."""

    def __init__(self):
        """Initialize Claude reorder client."""
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not set in environment variables")

        self.model = os.environ.get("REORDER_CLAUDE_MODEL", MODEL_ANALYZE)
        logger.info(f"Initialized Claude reorder client with model: {self.model}")

    def create_photo_tour_order(self, image_analysis, address):
        """Create optimal photo tour order, with chunked fallback.

        Strategy:
        1. Take the top-N images by usefulness_score (default 20) and try a
           single call for the whole set.
        2. If that fails, split the images into 2–3 chunks and call the model
           separately for each chunk.
        3. Concatenate the per-chunk tours into a single tour and normalize
           reorder_position.
        """
        logger.info(
            "Creating photo tour order for %s (%d images)",
            address,
            len(image_analysis),
        )

        if not image_analysis:
            logger.warning("No image_analysis data provided; cannot create tour")
            return None

        # Sort by usefulness_score and keep top N to keep prompt small
        try:
            sorted_images = sorted(
                image_analysis,
                key=lambda img: img.get("usefulness_score", 0),
                reverse=True,
            )
        except Exception:
            sorted_images = image_analysis

        max_images_for_prompt = 20
        limited_images = sorted_images[:max_images_for_prompt]

        # 1) Primary attempt: all selected images in one call
        primary_result = self._call_model_for_subset(
            limited_images,
            address,
            context_label="full-set",
        )
        if primary_result:
            return primary_result

        # 2) Chunked fallback
        num_images = len(limited_images)
        if num_images <= 8:
            # Very small set; if full-set failed there is little benefit in chunking
            logger.error(
                "Full-set reordering failed for small image set (%d images); "
                "giving up.",
                num_images,
            )
            return None

        # Decide how many chunks: 3 for larger sets, otherwise 2
        num_chunks = 3 if num_images >= 15 else 2
        chunk_size = max(1, (num_images + num_chunks - 1) // num_chunks)
        logger.warning(
            "Full-set reordering failed; attempting chunked fallback with %d "
            "chunks (chunk_size=%d)",
            num_chunks,
            chunk_size,
        )

        combined_tour = []
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min(start_idx + chunk_size, num_images)
            chunk = limited_images[start_idx:end_idx]
            if not chunk:
                continue

            chunk_label = f"chunk-{i+1}-of-{num_chunks}"
            logger.info(
                "Requesting tour segment for %s: images %d-%d of %d",
                chunk_label,
                start_idx + 1,
                end_idx,
                num_images,
            )

            chunk_result = self._call_model_for_subset(
                chunk,
                address,
                context_label=chunk_label,
            )

            if not chunk_result:
                logger.warning(
                    "No tour returned for %s; skipping this segment", chunk_label
                )
                continue

            segment = chunk_result.get("photo_tour_order", [])
            if not segment:
                logger.warning(
                    "Empty tour segment for %s; skipping this segment", chunk_label
                )
                continue

            combined_tour.extend(segment)

        if not combined_tour:
            logger.error(
                "Chunked fallback failed to produce any tour segments; giving up "
                "for %s",
                address,
            )
            return None

        # Normalize reorder_position across combined segments
        for idx, photo in enumerate(combined_tour, 1):
            photo["reorder_position"] = idx

        logger.info(
            "Chunked fallback produced combined tour with %d photos for %s",
            len(combined_tour),
            address,
        )

        # Synthesize a minimal result object so callers see a consistent shape
        return {
            "photo_tour_order": combined_tour,
            "tour_metadata": {
                "model_used": self.model,
                "created_at": time.time(),
                "chunked_fallback_used": True,
                "chunks_used": num_chunks,
                "source_images_considered": num_images,
            },
        }

    def _call_model_for_subset(self, images_subset, address, context_label="subset"):
        """Call Claude for a specific subset of images and parse the JSON response.

        Returns either a parsed dict with `photo_tour_order` or None on failure.
        """
        start_time = time.time()

        # Build compact text description for just this subset
        image_data_text = (
            f"AVAILABLE IMAGES for {context_label} (count={len(images_subset)}):\n\n"
        )
        for img in images_subset:
            desc = img.get("description", "No description")
            if desc and len(desc) > 256:
                desc = desc[:256] + "..."
            image_data_text += (
                f"[{img.get('image_index', 'N/A')}] "
                f"{img.get('image_type', 'unknown')} | "
                f"Score:{img.get('usefulness_score', 0)} | "
                f"{desc}\n"
            )

        user_prompt = (
            get_photo_reorder_prompt()
            + "\n\n"
            + image_data_text
            + "\nRespond with ONLY the final JSON object — no commentary, no code fences."
        )

        # DEBUG: write the prompt for this subset to a file so we can inspect
        # exactly what was sent for problematic properties.
        try:
            safe_addr = (
                address.replace("/", "_")
                .replace(",", "")
                .replace(" ", "_")
            )
            debug_dir = Path("output")
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / f"reorder_prompt_{safe_addr}_{context_label}.txt"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write("PHOTO REORDER PROMPT\n\n")
                f.write(get_photo_reorder_prompt())
                f.write("\n\n")
                f.write(image_data_text)
            logger.info(
                "Wrote debug prompt for %s (%s) to %s",
                address,
                context_label,
                debug_file,
            )
        except Exception as e:
            logger.warning(
                "Failed to write debug prompt for %s (%s): %s",
                address,
                context_label,
                e,
            )

        content = None
        try:
            content = vision_text(
                user_prompt,
                None,
                model=self.model,
                max_tokens=8000,
                system=REORDER_SYSTEM_PROMPT,
            )

            elapsed_time = time.time() - start_time
            logger.info(
                "Claude reordering (%s) complete for %s in %.1fs",
                context_label,
                address,
                elapsed_time,
            )

            if not content or len(content.strip()) == 0:
                logger.error(
                    "Empty response from Claude for %s (%s)",
                    address,
                    context_label,
                )
                return None

            logger.debug(
                "Reordering response length for %s: %d characters",
                context_label,
                len(content),
            )

            # Try to locate a JSON object in the content (in case model added text)
            json_str = content
            first_brace = content.find("{")
            last_brace = content.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = content[first_brace : last_brace + 1]

            result = json.loads(json_str)

            if "photo_tour_order" not in result:
                logger.error(
                    "Response missing 'photo_tour_order' field for %s (%s)",
                    address,
                    context_label,
                )
                return None

            tour = result.get("photo_tour_order", [])
            logger.info(
                "Created tour segment with %d photos for %s (%s)",
                len(tour),
                address,
                context_label,
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Claude response as JSON for %s (%s): %s",
                address,
                context_label,
                e,
            )
            logger.error(
                "Response content (first 1000 chars): %s",
                content[:1000] if content else "EMPTY",
            )
            return None

        except Exception as e:
            logger.error(
                "Claude API error for %s (%s): %s", address, context_label, e
            )
            return None

    def extract_photo_tour_order(self, reorder_result):
        """
        Extract and validate photo tour order from reorder result.

        Args:
            reorder_result: Parsed reorder result

        Returns:
            List of photos in tour order with reorder_position
        """
        photo_tour = reorder_result.get("photo_tour_order", [])

        if not photo_tour:
            logger.warning("No photo tour order found in model response")
            return []

        # Validate and ensure reorder_position is set correctly
        validated_tour = []
        for i, photo in enumerate(photo_tour, 1):
            validated_photo = photo.copy()
            # Ensure reorder_position matches the actual position
            validated_photo["reorder_position"] = i
            validated_tour.append(validated_photo)

        logger.info(f"Validated tour with {len(validated_tour)} photos")

        return validated_tour

    def get_tour_metadata(self, reorder_result):
        """
        Extract tour metadata from reorder result.

        Args:
            reorder_result: Parsed reorder result

        Returns:
            Dictionary of tour metadata
        """
        metadata = reorder_result.get("tour_metadata", {})

        # Add extraction metadata
        metadata["model_used"] = self.model
        metadata["created_at"] = time.time()

        return metadata
