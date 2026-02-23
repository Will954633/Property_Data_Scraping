#!/usr/bin/env python3
"""
Orchestrator Monitoring Dashboard
Last Updated: 31/01/2026, 8:09 am (Brisbane Time)

Real-time monitoring dashboard for the orchestrator and all workers.
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from pymongo import MongoClient

LOG_DIR = Path(__file__).parent / "orchestrator_logs"
STATE_FILE = LOG_DIR / "orchestrator_state.json"
ERROR_LOG = LOG_DIR / "errors.log"


def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')


def get_orchestrator_state():
    """Load orchestrator state"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None


def get_recent_errors(limit=10):
    """Get recent errors from error log"""
    if not ERROR_LOG.exists():
        return []
    
    try:
        with open(ERROR_LOG, 'r') as f:
            lines = f.readlines()
            return lines[-limit:] if lines else []
    except:
        return []


def get_database_stats():
    """Get current database statistics"""
    try:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = client['Gold_Coast']
        
        total_with_scraped = 0
        total_updated = 0
        suburb_stats = []
        
        for collection_name in db.list_collection_names():
            if collection_name == 'system.indexes':
                continue
            
            collection = db[collection_name]
            scraped = collection.count_documents({'scraped_data': {'$exists': True}})
            updated = collection.count_documents({'updated_at': {'$exists': True}})
            
            if scraped > 0:
                total_with_scraped += scraped
                total_updated += updated
                suburb_stats.append({
                    'suburb': collection_name,
                    'scraped': scraped,
                    'updated': updated,
                    'percent': (updated / scraped * 100) if scraped > 0 else 0
                })
        
        client.close()
        
        return {
            'total_properties': total_with_scraped,
            'updated': total_updated,
            'remaining': total_with_scraped - total_updated,
            'progress_percent': (total_updated / total_with_scraped * 100) if total_with_scraped > 0 else 0,
            'suburbs': sorted(suburb_stats, key=lambda x: x['updated'], reverse=True)
        }
    except Exception as e:
        return {'error': str(e)}


def format_duration(seconds):
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}h"
    else:
        return f"{seconds/86400:.1f}d"


def display_dashboard():
    """Display the monitoring dashboard"""
    clear_screen()
    
    print("=" * 80)
    print("GOLD COAST DATABASE UPDATE - ORCHESTRATOR DASHBOARD")
    print("=" * 80)
    print()
    
    # Get orchestrator state
    state = get_orchestrator_state()
    
    if not state:
        print("⚠️  Orchestrator not running or no state file found")
        print()
        print("To start the orchestrator:")
        print("  cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast")
        print("  python3 orchestrator.py")
        return
    
    # Orchestrator info
    start_time = datetime.fromisoformat(state['start_time']) if state.get('start_time') else None
    last_update = datetime.fromisoformat(state['last_update']) if state.get('last_update') else None
    
    print("📊 ORCHESTRATOR STATUS")
    print("-" * 80)
    if start_time:
        uptime = (datetime.now() - start_time).total_seconds()
        print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Uptime: {format_duration(uptime)}")
    if last_update:
        seconds_ago = (datetime.now() - last_update).total_seconds()
        print(f"  Last update: {seconds_ago:.0f}s ago")
        if seconds_ago > 120:
            print(f"  ⚠️  WARNING: No updates in {seconds_ago:.0f}s - orchestrator may be stuck")
    print()
    
    # Worker status
    workers = state.get('workers', [])
    running_workers = sum(1 for w in workers if w.get('running'))
    total_processed = sum(w.get('properties_processed', 0) for w in workers)
    
    print("👷 WORKER STATUS")
    print("-" * 80)
    print(f"  Total workers: {len(workers)}")
    print(f"  Running: {running_workers}/{len(workers)}")
    print(f"  Total processed: {total_processed:,} properties")
    print()
    
    # Top 10 workers by properties processed
    top_workers = sorted(workers, key=lambda x: x.get('properties_processed', 0), reverse=True)[:10]
    print("  Top 10 Workers:")
    for w in top_workers:
        worker_id = w.get('worker_id', '?')
        processed = w.get('properties_processed', 0)
        running = "✅" if w.get('running') else "❌"
        uptime = w.get('uptime_seconds', 0)
        print(f"    Worker {worker_id:2d}: {processed:6,d} properties | {running} | {format_duration(uptime)} uptime")
    print()
    
    # Database progress
    db_stats = get_database_stats()
    
    if 'error' in db_stats:
        print(f"⚠️  Database connection error: {db_stats['error']}")
    else:
        print("📈 DATABASE PROGRESS")
        print("-" * 80)
        print(f"  Total properties: {db_stats['total_properties']:,}")
        print(f"  Updated: {db_stats['updated']:,}")
        print(f"  Remaining: {db_stats['remaining']:,}")
        print(f"  Progress: {db_stats['progress_percent']:.2f}%")
        print()
        
        # Estimate completion
        if start_time and db_stats['updated'] > 0:
            elapsed_hours = (datetime.now() - start_time).total_seconds() / 3600
            rate = db_stats['updated'] / elapsed_hours if elapsed_hours > 0 else 0
            if rate > 0:
                remaining_hours = db_stats['remaining'] / rate
                completion_time = datetime.now() + timedelta(hours=remaining_hours)
                print(f"  Current rate: {rate:.0f} properties/hour")
                print(f"  Est. completion: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Time remaining: {format_duration(remaining_hours * 3600)}")
        print()
        
        # Top 10 suburbs by progress
        print("  Top 10 Suburbs by Updates:")
        for suburb in db_stats['suburbs'][:10]:
            name = suburb['suburb']
            updated = suburb['updated']
            total = suburb['scraped']
            percent = suburb['percent']
            print(f"    {name:30s}: {updated:6,d}/{total:6,d} ({percent:5.1f}%)")
    print()
    
    # Recent errors
    errors = get_recent_errors(5)
    if errors:
        print("⚠️  RECENT ERRORS (Last 5)")
        print("-" * 80)
        for error in errors:
            print(f"  {error.strip()}")
    else:
        print("✅ NO RECENT ERRORS")
    print()
    
    print("=" * 80)
    print(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Press Ctrl+C to exit")
    print("=" * 80)


def main():
    """Main monitoring loop"""
    try:
        while True:
            display_dashboard()
            time.sleep(10)  # Refresh every 10 seconds
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
