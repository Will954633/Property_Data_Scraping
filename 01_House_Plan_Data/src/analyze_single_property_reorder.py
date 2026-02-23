"""
Script to reorder photos for a single property.
This mirrors the floor plan single-property analysis pattern,
using the photo reordering GPT pipeline.
"""
import json
import re
import sys
import time
from typing import Optional

from gpt_reorder_client import GPTReorderClient
from mongodb_reorder_client import MongoDBReorderClient
from logger import logger
from main import PropertyValuationExtractor


OID_REGEX = re.compile(r"[0-9a-fA-F]{24}")


def extract_object_id(source: str) -> Optional[str]:
    """Extract a MongoDB ObjectId from a raw argument string.

    This is designed to be flexible so you can pass either:
    - A bare ObjectId: 693e8ea2ee434af1738b8f89
    - A Compass-style filename like:
      /property_data.properties_for_sale:{"$oid":"693e8ea2ee434af1738b8f89"}.json
    """
    if not source:
        return None

    # If they passed a bare ObjectId, just validate and return it
    if len(source) == 24 and OID_REGEX.fullmatch(source):
        return source

    # Otherwise, search inside the string for the first 24-char hex sequence
    match = OID_REGEX.search(source)
    if match:
        return match.group(0)

    return None


def reorder_single_property(raw_id: Optional[str] = None):
    """Run photo reordering for a single property.

    Args:
        raw_id: Optional raw identifier string. This can be:
            - A bare 24-char ObjectId string, or
            - A full exported JSON filename containing the $oid value.
            If None, the script will pick the first property that needs
            reordering (has image_analysis and no photo_tour_order).
    """
    logger.info("=" * 80)
    logger.info("PHOTO REORDERING - SINGLE PROPERTY TEST")
    logger.info("=" * 80)

    mongo_client = MongoDBReorderClient()
    gpt_client = GPTReorderClient()

    try:
        document = None

        if raw_id:
            object_id_str = extract_object_id(raw_id)
            if not object_id_str:
                logger.error(f"Could not extract a valid ObjectId from: {raw_id}")
                return

            logger.info(f"Looking up property by _id: {object_id_str}")
            document = mongo_client.get_document_by_id(object_id_str)
            if not document:
                logger.error(f"No document found in MongoDB with _id={object_id_str}")
                return
        else:
            logger.info("No id provided - will select the first property that needs reordering")
            document = mongo_client.get_single_document_for_reordering()
            if not document:
                logger.error("No documents found that require photo reordering")
                return

        # Basic document details
        doc_id = document.get("_id")
        address = (
            document.get("complete_address")
            or document.get("address")
            or document.get("scraped_data", {}).get("address")
            or "Unknown Address"
        )

        image_analysis = document.get("image_analysis", [])
        if not image_analysis:
            logger.info(
                "Document %s has no image_analysis yet – running single-property "
                "image analysis pipeline first",
                doc_id,
            )

            # Run the existing valuation/image-analysis pipeline for just this document
            extractor = PropertyValuationExtractor()
            if not extractor.initialize():
                logger.error("Failed to initialize PropertyValuationExtractor; aborting")
                return

            try:
                result = extractor.process_document(document)
            finally:
                # Make sure we close its Mongo client
                if extractor.mongo_client:
                    extractor.mongo_client.close()

            images_analyzed = 0
            if isinstance(result, dict):
                images_analyzed = result.get("images_analyzed") or 0

            if not images_analyzed:
                logger.error(
                    "Image analysis pipeline completed but no images were analyzed "
                    "for document %s; cannot proceed to photo reordering",
                    doc_id,
                )
                return

            # Re-fetch the document so we see the freshly-written image_analysis
            document = mongo_client.get_document_by_id(str(doc_id))
            if not document:
                logger.error(
                    "After image analysis, failed to reload document %s from MongoDB",
                    doc_id,
                )
                return

            image_analysis = document.get("image_analysis", [])
            if not image_analysis:
                logger.error(
                    "After image analysis, document %s still has no image_analysis; "
                    "cannot reorder photos",
                    doc_id,
                )
                return

        logger.info("")
        logger.info(f"Property: {address}")
        logger.info(f"Document _id: {doc_id}")
        logger.info(f"Images with analysis: {len(image_analysis)}")

        logger.info("\nStarting GPT photo reordering...")
        start_time = time.time()

        # Call GPT to build tour
        reorder_result = gpt_client.create_photo_tour_order(image_analysis, address)
        if not reorder_result:
            logger.error(
                "Photo reordering GPT call returned no result for %s; "
                "leaving document with image_analysis only",
                doc_id,
            )
            return

        photo_tour_order = gpt_client.extract_photo_tour_order(reorder_result)
        tour_metadata = gpt_client.get_tour_metadata(reorder_result)

        for photo in photo_tour_order:
            photo["tour_metadata"] = tour_metadata

        elapsed = time.time() - start_time

        # Update MongoDB
        mongo_client.update_with_photo_tour_order(
            doc_id,
            photo_tour_order,
            worker_id="single_property_test",
            processing_time=elapsed,
        )

        # Pretty print result to console
        logger.info("\n" + "=" * 80)
        logger.info("PHOTO TOUR ORDER RESULT")
        logger.info("=" * 80)
        print(json.dumps(photo_tour_order, indent=2, default=str))

        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Address: {address}")
        logger.info(f"Document _id: {doc_id}")
        logger.info(f"Photos in tour: {len(photo_tour_order)}")
        logger.info(f"Processing time: {elapsed:.1f}s")
        logger.info("Analysis complete! Please review the tour above.")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error during single-property photo reordering: {e}", exc_info=True)
        raise
    finally:
        mongo_client.close()


if __name__ == "__main__":
    # If an argument is provided, treat it as an id/filename; otherwise pick first pending doc
    if len(sys.argv) > 1:
        raw_id = " ".join(sys.argv[1:])
        logger.info(f"Running single-property photo reordering for id/filename: {raw_id}")
        reorder_single_property(raw_id)
    else:
        logger.info("No id specified - running on first property that needs reordering")
        reorder_single_property()
