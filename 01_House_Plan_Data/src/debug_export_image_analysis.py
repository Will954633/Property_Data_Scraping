"""Debug script to export image_analysis for a specific property and
compare it with a sample property that already has photo_tour_order.

Usage:
    cd 01_House_Plan_Data
    python src/debug_export_image_analysis.py 693e8ea2ee434af1738b8f89

This will write two files into output/:
    - debug_image_analysis_<bad_id>.json
    - debug_image_analysis_sample_reordered.json
"""
import json
import sys
from bson import ObjectId

from mongodb_reorder_client import MongoDBReorderClient
from logger import logger


def export_image_analysis(target_id_str: str | None = None) -> None:
    client = MongoDBReorderClient()
    try:
        if not target_id_str:
            logger.info(
                "No _id provided, please pass a Mongo ObjectId, e.g.: "
                "python src/debug_export_image_analysis.py 693e8ea2ee434af1738b8f89"
            )
            return

        try:
            target_id = ObjectId(target_id_str)
        except Exception:
            logger.error("%s is not a valid ObjectId", target_id_str)
            return

        # Fetch the problematic document
        bad_doc = client.collection.find_one({"_id": target_id})
        if not bad_doc:
            logger.error("No document found with _id=%s", target_id_str)
            return

        bad_out = {
            "_id": str(bad_doc.get("_id")),
            "address": (
                bad_doc.get("complete_address")
                or bad_doc.get("address")
                or bad_doc.get("scraped_data", {}).get("address")
                or "Unknown Address"
            ),
            "image_analysis_count": len(bad_doc.get("image_analysis", [])),
            "image_analysis": bad_doc.get("image_analysis", []),
        }

        bad_path = f"output/debug_image_analysis_{target_id_str}.json"
        with open(bad_path, "w") as f:
            json.dump(bad_out, f, indent=2, default=str)
        logger.info("Exported target image_analysis to %s", bad_path)

        # Fetch a comparison document that already has a photo_tour_order
        sample_query = {
            "image_analysis": {"$exists": True, "$ne": []},
            "photo_tour_order": {"$exists": True},
            "_id": {"$ne": target_id},
        }
        sample_doc = client.collection.find_one(sample_query)
        if not sample_doc:
            logger.warning(
                "No comparison document found with both image_analysis and "
                "photo_tour_order."
            )
            return

        sample_out = {
            "_id": str(sample_doc.get("_id")),
            "address": (
                sample_doc.get("complete_address")
                or sample_doc.get("address")
                or sample_doc.get("scraped_data", {}).get("address")
                or "Unknown Address"
            ),
            "image_analysis_count": len(sample_doc.get("image_analysis", [])),
            "image_analysis": sample_doc.get("image_analysis", []),
        }

        sample_path = "output/debug_image_analysis_sample_reordered.json"
        with open(sample_path, "w") as f:
            json.dump(sample_out, f, indent=2, default=str)
        logger.info("Exported sample comparison image_analysis to %s", sample_path)

    finally:
        client.close()


if __name__ == "__main__":
    target_id_arg = sys.argv[1] if len(sys.argv) > 1 else None
    export_image_analysis(target_id_arg)
