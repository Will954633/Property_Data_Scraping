"""
GPT Vision API client module for floor plan analysis.
"""
import json
import time
from typing import List, Dict, Any, Optional

from openai import OpenAI
from config import OPENAI_API_KEY, GPT_MODEL, MAX_TOKENS, REQUEST_TIMEOUT
from logger import logger
from prompts import get_floor_plan_analysis_prompt


class GPTFloorPlanClient:
    """Client for analyzing floor plans using OpenAI GPT Vision API.

    This client includes a fallback mechanism for the rare case where the
    model consumes the entire completion token budget on internal reasoning
    and returns an empty visible response (finish_reason='length',
    accepted_prediction_tokens=0). In that case, we will:

    1. Log the condition with usage statistics, and
    2. If there are multiple floor plan images, split them into two batches
       and send two separate prompts, then merge the results.
    """

    def __init__(self):
        """Initialize OpenAI client."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment variables")

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = GPT_MODEL
        logger.info(f"Initialized GPT client with model: {self.model}")

    # ------------------------------------------------------------------
    # Public entrypoint with fallback
    # ------------------------------------------------------------------
    def analyze_floor_plans(self, floor_plan_urls: List[str], address: str) -> Optional[Dict[str, Any]]:
        """Analyze floor plan images using GPT Vision API with fallback.

        Primary strategy:
          * Send all floor plan images in a single call.

        Fallback strategy (for empty responses caused by length limits):
          * If the primary call raises a ValueError("Empty response from GPT")
            _and_ there is more than one floor plan image, split the list into
            two halves and analyze each half separately.
          * Merge the resulting JSON objects into a single combined result.

        Args:
            floor_plan_urls: List of floor plan image URLs.
            address: Property address for logging.

        Returns:
            Parsed JSON response with floor plan data, or None if analysis
            cannot be performed.
        """
        if not floor_plan_urls:
            logger.warning(f"No floor plans provided for {address}")
            return None

        try:
            # First attempt: all floor plans in one request
            return self._analyze_floor_plans_once(floor_plan_urls, address, attempt_label="primary")

        except ValueError as e:
            # Only trigger fallback on our explicit empty-response error
            message = str(e)
            if "Empty response from GPT" not in message or len(floor_plan_urls) <= 1:
                logger.error(
                    f"No fallback available for error while analyzing {address}: {e}"
                )
                raise

            logger.warning(
                f"Empty GPT response for {address} with {len(floor_plan_urls)} floor plans. "
                f"Attempting fallback by splitting into two batches."
            )

            mid = len(floor_plan_urls) // 2
            first_batch = floor_plan_urls[:mid]
            second_batch = floor_plan_urls[mid:]

            results = []

            # Analyze first half
            if first_batch:
                try:
                    res1 = self._analyze_floor_plans_once(
                        first_batch,
                        f"{address} (part 1/2)",
                        attempt_label="fallback_split_1",
                    )
                    if res1:
                        results.append((first_batch, res1))
                except Exception as e1:  # noqa: BLE001
                    logger.error(
                        f"Fallback part 1 failed for {address}: {e1}",
                        exc_info=True,
                    )

            # Analyze second half
            if second_batch:
                try:
                    res2 = self._analyze_floor_plans_once(
                        second_batch,
                        f"{address} (part 2/2)",
                        attempt_label="fallback_split_2",
                    )
                    if res2:
                        results.append((second_batch, res2))
                except Exception as e2:  # noqa: BLE001
                    logger.error(
                        f"Fallback part 2 failed for {address}: {e2}",
                        exc_info=True,
                    )

            if not results:
                logger.error(
                    f"All fallback attempts failed for {address}; giving up on this property."
                )
                raise

            if len(results) == 1:
                # Only one half succeeded; annotate metadata and return it
                batch_urls, single_result = results[0]
                logger.warning(
                    f"Only one fallback batch succeeded for {address} "
                    f"({len(batch_urls)} floor plan(s)). Returning partial analysis."
                )

                meta = single_result.setdefault("analysis_metadata", {})
                meta.update(
                    {
                        "fallback_used": True,
                        "fallback_mode": "split_batches_partial",
                        "floor_plan_count": len(floor_plan_urls),
                        "floor_plan_urls": floor_plan_urls,
                    }
                )
                return single_result

            # Both halves succeeded; merge results
            logger.info(
                f"Both fallback batches succeeded for {address}. "
                f"Merging results from {len(first_batch)} + {len(second_batch)} floor plan(s)."
            )

            merged = self._merge_floor_plan_results(
                floor_plan_urls=floor_plan_urls,
                primary_result=results[0][1],
                secondary_result=results[1][1],
            )
            return merged

    # ------------------------------------------------------------------
    # Internal single-call analysis
    # ------------------------------------------------------------------
    def _analyze_floor_plans_once(
        self,
        floor_plan_urls: List[str],
        address: str,
        attempt_label: str = "primary",
    ) -> Dict[str, Any]:
        """Perform a single GPT Vision call for the given floor plans.

        This is essentially the original implementation, with enhanced
        logging around empty responses and finish_reason.
        """
        logger.info(
            f"Analyzing {len(floor_plan_urls)} floor plan(s) for {address} "
            f"[attempt={attempt_label}]"
        )
        start_time = time.time()

        # Prepare messages with floor plan images
        message_content: List[Dict[str, Any]] = [
            {"type": "text", "text": get_floor_plan_analysis_prompt()}
        ]

        # Add floor plan images to message
        for url in floor_plan_urls:
            message_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        # Use high detail for floor plans to capture measurements
                        "detail": "high",
                    },
                }
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional floor plan analyst with expertise "
                    "in architectural drawings, property measurements, and "
                    "real estate analysis."
                ),
            },
            {"role": "user", "content": message_content},
        ]

        try:
            # Call GPT API
            # Note: gpt-5-nano only supports default temperature=1, so we omit
            # the temperature parameter. We do, however, enforce a timeout
            # based on REQUEST_TIMEOUT from config.
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
                timeout=REQUEST_TIMEOUT,
            )

            elapsed_time = time.time() - start_time
            logger.info(
                f"GPT analysis complete for {address} ({elapsed_time:.1f}s, "
                f"attempt={attempt_label})"
            )

            choice = response.choices[0]
            content = (choice.message.content or "").strip()
            finish_reason = choice.finish_reason

            # Log finish_reason and usage for diagnostics
            logger.debug(
                "GPT usage for %s [attempt=%s]: finish_reason=%s, usage=%s",
                address,
                attempt_label,
                finish_reason,
                getattr(response, "usage", None),
            )

            # Handle empty content explicitly
            if not content:
                logger.error(f"Empty response from GPT for {address} [attempt={attempt_label}]")
                logger.error(f"Full response object: {response}")
                raise ValueError("Empty response from GPT")

            logger.debug(f"Response length: {len(content)} characters")

            result: Dict[str, Any] = json.loads(content)

            # Add/augment metadata
            analysis_metadata = result.get("analysis_metadata", {}) or {}
            analysis_metadata.update(
                {
                    "model_used": self.model,
                    "analyzed_at": time.time(),
                    "analysis_duration_seconds": elapsed_time,
                    "floor_plan_count": len(floor_plan_urls),
                    "floor_plan_urls": floor_plan_urls,
                    "finish_reason": finish_reason,
                    "attempt_label": attempt_label,
                }
            )
            result["analysis_metadata"] = analysis_metadata

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}")
            logger.error(
                "Response content (first 1000 chars): %s",
                content[:1000] if "content" in locals() and content else "EMPTY",
            )
            logger.error(
                "Response content (last 500 chars): %s",
                content[-500:]
                if "content" in locals() and content and len(content) > 500
                else "",
            )
            raise

        except Exception as e:  # noqa: BLE001
            logger.error(f"GPT API error for {address}: {e}")
            raise

    # ------------------------------------------------------------------
    # Result-merging helpers for split fallback
    # ------------------------------------------------------------------
    def _merge_floor_plan_results(
        self,
        floor_plan_urls: List[str],
        primary_result: Dict[str, Any],
        secondary_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge two floor plan analysis results into a single object.

        This is a pragmatic merge strategy tailored to the expected schema
        from `get_floor_plan_analysis_prompt()`:

        * `rooms`, `outdoor_spaces`, `additional_features` -> concatenated.
        * Bedroom/bathroom/parking counts -> summed where numeric.
        * Floor areas -> choose the non-null value with higher confidence;
          if both non-null and same confidence, prefer the larger area.
        * `buyer_insights`, `layout_features`, `data_quality` -> prefer the
          primary result, but augment list fields where possible.

        The merged result will have consolidated `analysis_metadata` that
        indicates a split-batch fallback was used.
        """

        def _sum_if_number(a: Any, b: Any) -> Optional[float]:
            vals = [v for v in (a, b) if isinstance(v, (int, float))]
            return float(sum(vals)) if vals else None

        def _choose_area_block(key: str) -> Optional[Dict[str, Any]]:
            a = primary_result.get(key) or {}
            b = secondary_result.get(key) or {}

            def conf_val(block: Dict[str, Any]) -> int:
                conf = (block or {}).get("confidence")
                mapping = {"low": 1, "medium": 2, "high": 3}
                return mapping.get(conf, 0)

            ca, cb = conf_val(a), conf_val(b)
            va, vb = a.get("value"), b.get("value")

            if ca > cb:
                return a
            if cb > ca:
                return b

            # Same confidence (or none) -> choose non-null with larger value
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                return a if va >= vb else b
            if va is not None and vb is None:
                return a
            if vb is not None and va is None:
                return b

            # Fallback: prefer primary
            return a or b or None

        merged: Dict[str, Any] = {}

        # 1) Directly merge simple structured counts
        bedrooms_a = primary_result.get("bedrooms") or {}
        bedrooms_b = secondary_result.get("bedrooms") or {}
        merged["bedrooms"] = {
            "total_count": _sum_if_number(
                bedrooms_a.get("total_count"), bedrooms_b.get("total_count")
            )
            or bedrooms_a.get("total_count")
            or bedrooms_b.get("total_count"),
            "details": "; ".join(
                [
                    v
                    for v in (
                        bedrooms_a.get("details"), bedrooms_b.get("details")
                    )
                    if v
                ]
            )
            or bedrooms_a.get("details")
            or bedrooms_b.get("details"),
        }

        bathrooms_a = primary_result.get("bathrooms") or {}
        bathrooms_b = secondary_result.get("bathrooms") or {}
        merged["bathrooms"] = {
            "total_count": _sum_if_number(
                bathrooms_a.get("total_count"), bathrooms_b.get("total_count")
            )
            or bathrooms_a.get("total_count")
            or bathrooms_b.get("total_count"),
            "full_bathrooms": _sum_if_number(
                bathrooms_a.get("full_bathrooms"),
                bathrooms_b.get("full_bathrooms"),
            )
            or bathrooms_a.get("full_bathrooms")
            or bathrooms_b.get("full_bathrooms"),
            "powder_rooms": _sum_if_number(
                bathrooms_a.get("powder_rooms"), bathrooms_b.get("powder_rooms")
            )
            or bathrooms_a.get("powder_rooms")
            or bathrooms_b.get("powder_rooms"),
            "ensuites": _sum_if_number(
                bathrooms_a.get("ensuites"), bathrooms_b.get("ensuites")
            )
            or bathrooms_a.get("ensuites")
            or bathrooms_b.get("ensuites"),
            "details": "; ".join(
                [
                    v
                    for v in (
                        bathrooms_a.get("details"), bathrooms_b.get("details")
                    )
                    if v
                ]
            )
            or bathrooms_a.get("details")
            or bathrooms_b.get("details"),
        }

        parking_a = primary_result.get("parking") or {}
        parking_b = secondary_result.get("parking") or {}
        merged["parking"] = {
            "garage_spaces": _sum_if_number(
                parking_a.get("garage_spaces"), parking_b.get("garage_spaces")
            )
            or parking_a.get("garage_spaces")
            or parking_b.get("garage_spaces"),
            "carport_spaces": _sum_if_number(
                parking_a.get("carport_spaces"), parking_b.get("carport_spaces")
            )
            or parking_a.get("carport_spaces")
            or parking_b.get("carport_spaces"),
            "total_spaces": _sum_if_number(
                parking_a.get("total_spaces"), parking_b.get("total_spaces")
            )
            or parking_a.get("total_spaces")
            or parking_b.get("total_spaces"),
            "garage_type": parking_a.get("garage_type")
            or parking_b.get("garage_type"),
            "notes": "; ".join(
                [
                    v
                    for v in (parking_a.get("notes"), parking_b.get("notes"))
                    if v
                ]
            )
            or parking_a.get("notes")
            or parking_b.get("notes"),
        }

        # 2) Areas
        for key in ("internal_floor_area", "total_floor_area", "total_land_area"):
            chosen = _choose_area_block(key)
            if chosen is not None:
                merged[key] = chosen

        # 3) Levels: prefer primary, but if both have details, concatenate
        levels_a = primary_result.get("levels") or {}
        levels_b = secondary_result.get("levels") or {}
        level_details = []
        if isinstance(levels_a.get("level_details"), list):
            level_details.extend(levels_a["level_details"])
        if isinstance(levels_b.get("level_details"), list):
            level_details.extend(levels_b["level_details"])

        merged["levels"] = {
            "total_levels": _sum_if_number(
                levels_a.get("total_levels"), levels_b.get("total_levels")
            )
            or levels_a.get("total_levels")
            or levels_b.get("total_levels"),
            "level_details": level_details,
        }

        # 4) List-like fields: concatenate
        def _concat_list_field(key: str) -> None:
            a = primary_result.get(key) or []
            b = secondary_result.get(key) or []
            merged[key] = []
            if isinstance(a, list):
                merged[key].extend(a)
            if isinstance(b, list):
                merged[key].extend(b)

        _concat_list_field("rooms")
        _concat_list_field("outdoor_spaces")
        _concat_list_field("additional_features")

        # 5) Buyer insights, layout features, data quality
        buyer_a = primary_result.get("buyer_insights") or {}
        buyer_b = secondary_result.get("buyer_insights") or {}
        merged["buyer_insights"] = {
            "ideal_for": list(
                (buyer_a.get("ideal_for") or []) + (buyer_b.get("ideal_for") or [])
            ),
            "key_benefits": list(
                (buyer_a.get("key_benefits") or [])
                + (buyer_b.get("key_benefits") or [])
            ),
            "considerations": list(
                (buyer_a.get("considerations") or [])
                + (buyer_b.get("considerations") or [])
            ),
            "lifestyle_suitability": buyer_a.get("lifestyle_suitability")
            or buyer_b.get("lifestyle_suitability"),
        }

        layout_a = primary_result.get("layout_features") or {}
        layout_b = secondary_result.get("layout_features") or {}
        merged["layout_features"] = {
            "open_plan": layout_a.get("open_plan")
            if layout_a.get("open_plan") is not None
            else layout_b.get("open_plan"),
            "split_level": layout_a.get("split_level")
            if layout_a.get("split_level") is not None
            else layout_b.get("split_level"),
            "flow_description": layout_a.get("flow_description")
            or layout_b.get("flow_description"),
            "highlights": list(
                (layout_a.get("highlights") or [])
                + (layout_b.get("highlights") or [])
            ),
        }

        dq_a = primary_result.get("data_quality") or {}
        dq_b = secondary_result.get("data_quality") or {}
        merged["data_quality"] = {
            "floor_plan_clarity": dq_a.get("floor_plan_clarity")
            or dq_b.get("floor_plan_clarity"),
            "measurements_available": dq_a.get("measurements_available")
            if dq_a.get("measurements_available") is not None
            else dq_b.get("measurements_available"),
            "missing_information": list(
                (dq_a.get("missing_information") or [])
                + (dq_b.get("missing_information") or [])
            ),
            "confidence_overall": dq_a.get("confidence_overall")
            or dq_b.get("confidence_overall"),
        }

        # 6) Metadata: start from primary, merge in secondary and fallback flags
        meta_a = primary_result.get("analysis_metadata", {}) or {}
        meta_b = secondary_result.get("analysis_metadata", {}) or {}
        merged_meta = {**meta_a, **meta_b}
        merged_meta.update(
            {
                "fallback_used": True,
                "fallback_mode": "split_batches_merged",
                "floor_plan_count": len(floor_plan_urls),
                "floor_plan_urls": floor_plan_urls,
            }
        )
        merged["analysis_metadata"] = merged_meta

        return merged
