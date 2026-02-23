#!/usr/bin/env python3
# Last Updated: 23/02/2026 - Production photo reorder for Gold_Coast_Currently_For_Sale
"""
Production runner for GPT photo reordering.
Processes properties from Gold_Coast_Currently_For_Sale.[suburb] that have
ollama_image_analysis but no photo_tour_order yet.

Usage:
    python3 run_photo_reorder.py --collection robina
    python3 run_photo_reorder.py --collection robina --workers 4
"""
import argparse
import os
import sys
import time
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load .env (OPENAI_API_KEY lives here)
load_dotenv()

# Add 01_House_Plan_Data/src to path to import GPTReorderClient
REORDER_SRC = os.path.join(
    os.path.dirname(__file__),
    '..', '..', '..', '01_House_Plan_Data', 'src'
)
sys.path.insert(0, os.path.abspath(REORDER_SRC))
from gpt_reorder_client import GPTReorderClient


def get_mongo_client():
    uri = (
        os.environ.get('COSMOS_CONNECTION_STRING') or
        os.environ.get('MONGODB_URI') or
        'mongodb://localhost:27017/'
    )
    return MongoClient(uri, retryWrites=False, tls=True, tlsAllowInvalidCertificates=True)


def process_collection(collection_name: str, workers: int = 2):
    print(f"[{datetime.now():%H:%M:%S}] Starting photo reorder for: {collection_name}")

    client = get_mongo_client()
    col = client['Gold_Coast_Currently_For_Sale'][collection_name]
    gpt = GPTReorderClient()

    # Find properties with image analysis but no photo_tour_order
    processed = 0
    skipped = 0
    errors = 0

    for doc in col.find({}):
        # Skip if already has photo_tour_order
        if doc.get('photo_tour_order'):
            skipped += 1
            continue

        image_analysis = doc.get('ollama_image_analysis')
        if not image_analysis or not isinstance(image_analysis, list) or len(image_analysis) == 0:
            skipped += 1
            continue

        address = doc.get('address', str(doc['_id']))

        try:
            reorder_result = gpt.create_photo_tour_order(image_analysis, address)
            if reorder_result is None:
                print(f"  ⚠️  No reorder result for {address}")
                errors += 1
                continue

            photo_tour_order = gpt.extract_photo_tour_order(reorder_result)
            if not photo_tour_order:
                print(f"  ⚠️  Empty tour order for {address}")
                errors += 1
                continue

            tour_metadata = gpt.get_tour_metadata(reorder_result)
            for photo in photo_tour_order:
                photo['tour_metadata'] = tour_metadata

            col.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'photo_tour_order': photo_tour_order,
                    'photo_tour_order_updated': datetime.now().isoformat()
                }}
            )
            processed += 1
            print(f"  ✅ {address} ({len(photo_tour_order)} photos ordered)")

        except Exception as e:
            print(f"  ❌ Error processing {address}: {e}")
            errors += 1

    client.close()
    print(f"[{datetime.now():%H:%M:%S}] {collection_name}: processed={processed} skipped={skipped} errors={errors}")
    return errors == 0 or processed > 0


def main():
    parser = argparse.ArgumentParser(description='Production photo reorder for Gold Coast properties')
    parser.add_argument('--collection', required=True, help='Collection name (suburb)')
    parser.add_argument('--workers', type=int, default=2, help='Unused - kept for CLI compat')
    args = parser.parse_args()

    success = process_collection(args.collection, args.workers)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
