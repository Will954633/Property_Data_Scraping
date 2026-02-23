import pymongo
from datetime import datetime
import json
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PropertyDB:
    def __init__(self, connection_string: str = "mongodb://127.0.0.1:27017/", db_name: str = "property_data"):
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client[db_name]
        self.properties = self.db['properties']  # Current for-sale properties
        self.snapshots = self.db['property_snapshots']  # Historical detailed data
        self.changes = self.db['property_changes']  # Change logs
        self.ensure_indexes()

    def ensure_indexes(self):
        """Create necessary indexes for performance"""
        self.properties.create_index("address", unique=True)
        self.properties.create_index("status")
        self.properties.create_index("last_seen")
        self.snapshots.create_index("property_id")
        self.snapshots.create_index("snapshot_date")
        self.changes.create_index("property_id")
        self.changes.create_index("change_date")
        logger.info("Indexes ensured")

    def get_all_active_addresses(self) -> List[str]:
        """Get list of addresses currently for sale"""
        active = self.properties.find({"status": "for_sale"})
        return [doc["address"] for doc in active]

    def update_daily_list(self, new_properties: List[Dict]) -> Dict[str, int]:
        """Update the properties collection with daily scrape results
        Returns stats: new, updated, removed
        """
        stats = {"new": 0, "updated": 0, "removed": 0, "total_processed": len(new_properties)}
        today = datetime.now()

        # Get current addresses in DB
        current_docs = {doc["address"]: doc for doc in self.properties.find({})}

        # Process new scrape
        new_addresses = {prop["address"] for prop in new_properties}
        db_addresses = set(current_docs.keys())

        # New properties
        new_addrs = new_addresses - db_addresses
        for addr in new_addrs:
            prop = next(p for p in new_properties if p["address"] == addr)
            prop["status"] = "for_sale"
            prop["first_seen"] = today
            prop["last_seen"] = today
            prop["last_detailed_update"] = None
            self.properties.insert_one(prop)
            stats["new"] += 1
            logger.info(f"New property added: {addr}")

        # Updated existing (still for sale)
        existing_addrs = new_addresses & db_addresses
        for addr in existing_addrs:
            prop = next(p for p in new_properties if p["address"] == addr)
            current = current_docs[addr]
            current["last_seen"] = today
            # Update basic fields if changed (e.g., price, beds)
            for key in ["bedrooms", "bathrooms", "parking", "land_size_sqm", "property_type", "price", "price_type", "agency", "agent", "inspection", "auction_date", "selling_method", "selling_description", "under_offer"]:
                if prop.get(key) != current.get(key):
                    current[key] = prop.get(key)
                    if key in ["price", "selling_description"]:
                        self.log_change(addr, key, current.get(key, "N/A"), prop.get(key), "daily_update")
            self.properties.replace_one({"address": addr}, current)
            stats["updated"] += 1

        # Removed properties (in DB but not in new scrape)
        removed_addrs = db_addresses - new_addresses
        for addr in removed_addrs:
            doc = current_docs[addr]
            doc["status"] = "removed"
            doc["last_seen"] = today
            self.properties.replace_one({"address": addr}, doc)
            stats["removed"] += 1
            logger.info(f"Property removed: {addr}")

        # Clean up old removed (optional, keep for history)
        # self.properties.delete_many({"status": "removed", "last_seen": {"$lt": today - timedelta(days=30)}})

        logger.info(f"Daily update complete: {stats}")
        return stats

    def store_detailed_snapshot(self, address: str, detailed_data: Dict, property_id: Optional[str] = None) -> str:
        """Store a detailed snapshot, return the snapshot _id"""
        today = datetime.now()
        snapshot = {
            "address": address,
            "snapshot_date": today,
            "data": detailed_data,
            "source": "script_b"
        }
        if property_id:
            snapshot["property_id"] = property_id
        result = self.snapshots.insert_one(snapshot)
        logger.info(f"Snapshot stored for {address}: {result.inserted_id}")
        return str(result.inserted_id)

    def get_latest_snapshot(self, address: str) -> Optional[Dict]:
        """Get the most recent snapshot for an address"""
        latest = self.snapshots.find_one(
            {"address": address},
            sort=[("snapshot_date", pymongo.DESCENDING)]
        )
        return latest

    def detect_and_log_changes(self, address: str, new_data: Dict, property_id: Optional[str] = None):
        """Compare new detailed data with previous snapshot and log changes"""
        prev_snapshot = self.get_latest_snapshot(address)
        if not prev_snapshot:
            logger.info(f"No previous snapshot for {address}, no changes to detect")
            return

        prev_data = prev_snapshot["data"]
        changes_logged = 0

        # Fields to compare for changes
        compare_fields = [
            "price", "description", "bedrooms", "bathrooms", "parking", "land_size_sqm",
            "property_type", "agent_name", "features", "inspection_times"
        ]

        for field in compare_fields:
            prev_val = prev_data.get(field, None)
            new_val = new_data.get(field, None)

            if prev_val != new_val:
                change_doc = {
                    "property_id": property_id,
                    "address": address,
                    "change_date": datetime.now(),
                    "change_type": field,
                    "old_value": prev_val,
                    "new_value": new_val,
                    "details": f"Changed from {prev_val} to {new_val}"
                }
                self.changes.insert_one(change_doc)
                changes_logged += 1
                logger.info(f"Change detected for {address} in {field}: {prev_val} -> {new_val}")

        if changes_logged > 0:
            # Update last_detailed_update in properties
            self.properties.update_one(
                {"address": address},
                {"$set": {"last_detailed_update": datetime.now()}}
            )
        else:
            logger.info(f"No changes detected for {address}")

    def log_error(self, address: str, error_type: str, error_msg: str, metadata: Dict = None):
        """Log an error with verbose metadata"""
        error_doc = {
            "address": address,
            "error_date": datetime.now(),
            "error_type": error_type,
            "error_message": error_msg,
            "metadata": metadata or {}
        }
        self.db['errors'].insert_one(error_doc)  # Separate errors collection
        logger.error(f"Error for {address}: {error_type} - {error_msg}")

    def close(self):
        self.client.close()
