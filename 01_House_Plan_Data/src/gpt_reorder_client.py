"""
GPT client for photo reordering system.
"""
import json
import time
from pathlib import Path
from openai import OpenAI
from config import OPENAI_API_KEY, GPT_REORDER_MODEL, MAX_TOKENS
from logger import logger
from prompts_reorder import get_photo_reorder_prompt

class GPTReorderClient:
    """Client for interacting with OpenAI GPT API for photo reordering."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = GPT_REORDER_MODEL
        logger.info(f"Initialized GPT Reorder client with model: {self.model}")
    
    def create_photo_tour_order(self, image_analysis, address):
        """Create optimal photo tour order using GPT, with chunked fallback.

        Strategy:
        1. Take the top-N images by usefulness_score (default 20) and try a
           single GPT call for the whole set.
        2. If that fails (e.g. empty content / length issues), split the
           images into 2–3 chunks and call GPT separately for each chunk.
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
        primary_result = self._call_gpt_for_subset(
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
                "Full-set GPT reordering failed for small image set (%d images); "
                "giving up.",
                num_images,
            )
            return None

        # Decide how many chunks: 3 for larger sets, otherwise 2
        num_chunks = 3 if num_images >= 15 else 2
        chunk_size = max(1, (num_images + num_chunks - 1) // num_chunks)
        logger.warning(
            "Full-set GPT reordering failed; attempting chunked fallback with %d "
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

            chunk_result = self._call_gpt_for_subset(
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

    def _call_gpt_for_subset(self, images_subset, address, context_label="subset"):
        """Call GPT for a specific subset of images and parse the JSON response.

        This encapsulates the JSON-mode call and the non-JSON fallback, and
        returns either a parsed dict with `photo_tour_order` or None on failure.
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

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a real estate photography expert specializing in "
                    "creating optimal virtual property tours."
                ),
            },
            {
                "role": "user",
                "content": get_photo_reorder_prompt() + "\n\n" + image_data_text,
            },
        ]

        # DEBUG: write the prompt for this subset to a file so we can inspect
        # exactly what was sent to GPT for problematic properties.
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

        try:
            # Primary attempt: strict JSON mode
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
            )

            elapsed_time = time.time() - start_time
            logger.info(
                "GPT reordering (%s) complete for %s in %.1fs (mode=json_object)",
                context_label,
                address,
                elapsed_time,
            )

            content = response.choices[0].message.content
            finish_reason = getattr(response.choices[0], "finish_reason", None)

            if not content or len(content.strip()) == 0:
                logger.warning(
                    "Empty response from GPT for %s (%s) in json_object mode "
                    "(finish_reason=%s) – will retry without response_format.",
                    address,
                    context_label,
                    finish_reason,
                )

                # Fallback: retry without response_format and explicitly ask for JSON
                fallback_messages = messages + [
                    {
                        "role": "user",
                        "content": (
                            "Your previous answer was truncated. "
                            "Respond again with ONLY the final JSON object and "
                            "nothing else (no commentary, no code fences)."
                        ),
                    }
                ]
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=fallback_messages,
                )
                content = response.choices[0].message.content
                finish_reason = getattr(response.choices[0], "finish_reason", None)

            # After fallback (if any), if still empty, try a final model-level
            # fallback to gpt-4.1-mini before giving up.
            if not content or len(content.strip()) == 0:
                logger.error(
                    "Empty response from GPT for %s (%s) even after fallback "
                    "(finish_reason=%s)",
                    address,
                    context_label,
                    finish_reason,
                )
                logger.error("Full response object: %s", response)

                # Model-level fallback: try a smaller, general chat model that
                # is less prone to reasoning-only completions.
                alt_model = "gpt-4.1-mini"
                logger.info(
                    "Falling back to alternate model %s for %s (%s)",
                    alt_model,
                    address,
                    context_label,
                )
                try:
                    alt_response = self.client.chat.completions.create(
                        model=alt_model,
                        messages=messages,
                    )
                    alt_content = alt_response.choices[0].message.content
                    alt_finish = getattr(
                        alt_response.choices[0], "finish_reason", None
                    )
                    if not alt_content or len(alt_content.strip()) == 0:
                        logger.error(
                            "Alternate model %s also returned empty response "
                            "for %s (%s) (finish_reason=%s)",
                            alt_model,
                            address,
                            context_label,
                            alt_finish,
                        )
                        logger.error("Alt full response object: %s", alt_response)
                        return None

                    logger.info(
                        "Alternate model %s produced a response for %s (%s)",
                        alt_model,
                        address,
                        context_label,
                    )
                    content = alt_content
                except Exception as e:
                    logger.error(
                        "Alternate model %s failed for %s (%s): %s",
                        alt_model,
                        address,
                        context_label,
                        e,
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
                "Failed to parse GPT response as JSON for %s (%s): %s",
                address,
                context_label,
                e,
            )
            logger.error(
                "Response content (first 1000 chars): %s",
                content[:1000] if "content" in locals() and content else "EMPTY",
            )
            return None

        except Exception as e:
            logger.error(
                "GPT API error for %s (%s): %s", address, context_label, e
            )
            return None

    def extract_photo_tour_order(self, reorder_result):
        """
        Extract and validate photo tour order from GPT result.
        
        Args:
            reorder_result: Parsed GPT reorder result
            
        Returns:
            List of photos in tour order with reorder_position
        """
        photo_tour = reorder_result.get("photo_tour_order", [])
        
        if not photo_tour:
            logger.warning("No photo tour order found in GPT response")
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
            reorder_result: Parsed GPT reorder result
            
        Returns:
            Dictionary of tour metadata
        """
        metadata = reorder_result.get("tour_metadata", {})
        
        # Add extraction metadata
        metadata["model_used"] = self.model
        metadata["created_at"] = time.time()
        
        return metadata
