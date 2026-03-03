#!/usr/bin/env python3
"""
Dynamic Suburb Spawning with Parallel Property Scraping
Last Updated: 06/02/2026, 3:15 pm (Friday) - Brisbane Time
- CRITICAL FIX: Added flush=True to all print() calls and sys.stdout reconfigure
  to ensure output is visible when launched via subprocess.Popen (orchestrator).
  Without this, Python buffers stdout when it's a pipe (not a TTY), causing the
  orchestrator to think the process is hung when it's actually working fine.

Previous Updates:
- 31/01/2026, 1:07 pm (Brisbane Time)

PURPOSE:
Combines BOTH optimizations for maximum performance:
1. Dynamic suburb spawning - maintains max 5 concurrent suburbs
2. Parallel property scraping - 3 properties at once per suburb
3. Auto-spawns new suburb when one completes

USAGE:
python3 run_dynamic_10_suburbs.py --test  # Test with 10 suburbs
python3 run_dynamic_10_suburbs.py --all   # All 52 suburbs
"""

import sys
import time
import json
import argparse
import subprocess
from multiprocessing import Process, Queue, Manager
from datetime import datetime

# CRITICAL: Force unbuffered stdout so output is visible when launched via subprocess.Popen
# Without this, Python buffers stdout when it's a pipe (not a TTY), causing the orchestrator
# to think the process is hung. This is the #1 reason for "scraping hang" issues.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

# Import the parallel suburb scraper
from run_parallel_suburb_scrape import run_suburb_scraper, monitor_progress


def load_suburbs_from_json(filename='gold_coast_suburbs.json'):
    """Load suburbs from JSON file"""
    with open(filename, 'r') as f:
        data = json.load(f)
    return [(s['name'], s['postcode']) for s in data['suburbs']]


def cleanup_zombie_chrome_processes():
    """
    Kill any zombie Chrome/ChromeDriver processes to prevent resource exhaustion.
    This is a self-healing mechanism that runs after each scraping session.
    """
    print("\n" + "=" * 80, flush=True)
    print("🧹 CLEANING UP ZOMBIE CHROME PROCESSES", flush=True)
    print("=" * 80 + "\n", flush=True)

    try:
        # Count existing processes
        check_cmd = "ps aux | grep -E 'chrome|chromedriver' | grep -v grep | wc -l"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        zombie_count = int(result.stdout.strip())

        if zombie_count > 0:
            print(f"Found {zombie_count} Chrome/ChromeDriver processes", flush=True)

            # Kill all Chrome and ChromeDriver processes
            kill_cmd = "killall -9 chrome chromedriver 2>/dev/null || true"
            subprocess.run(kill_cmd, shell=True)

            time.sleep(2)

            # Verify cleanup
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            remaining = int(result.stdout.strip())

            if remaining == 0:
                print(f"✅ Successfully killed {zombie_count} zombie processes", flush=True)
            else:
                print(f"⚠️ Killed processes but {remaining} still remain", flush=True)
        else:
            print("✅ No zombie processes found - system is clean", flush=True)

    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}", flush=True)

    print("\n" + "=" * 80 + "\n", flush=True)


def run_dynamic_scraping(suburbs, max_concurrent=5, parallel_properties=3):
    """
    Run dynamic suburb scraping with auto-spawning
    
    Args:
        suburbs: List of (name, postcode) tuples
        max_concurrent: Maximum concurrent suburb processes
        parallel_properties: Number of properties to scrape simultaneously per suburb
    """
    print("\n" + "=" * 80)
    print("DYNAMIC SUBURB SCRAPING WITH PARALLEL PROPERTIES")
    print("=" * 80)
    print(f"\nTotal Suburbs: {len(suburbs)}")
    print(f"Max Concurrent: {max_concurrent} suburbs at a time")
    print(f"Parallel Properties: {parallel_properties} properties at once per suburb")
    print(f"Strategy: Auto-spawn new suburb when one completes")
    print(f"\nEstimated Time: {len(suburbs) * 2 // max_concurrent} - {len(suburbs) * 3 // max_concurrent} minutes")
    print("=" * 80 + "\n")
    
    # Create shared progress queue and results dict
    manager = Manager()
    progress_queue = manager.Queue()
    results_dict = manager.dict()
    
    # Track active processes and pending suburbs
    active_processes = {}  # {suburb_name: Process}
    pending_suburbs = list(suburbs)  # Queue of suburbs to process
    completed_suburbs = []
    start_time = time.time()
    
    # Start initial batch
    print(f"Starting initial batch of {min(max_concurrent, len(pending_suburbs))} suburbs...\n")
    for i in range(min(max_concurrent, len(pending_suburbs))):
        suburb_name, postcode = pending_suburbs.pop(0)
        p = Process(target=run_suburb_scraper, args=(suburb_name, postcode, progress_queue, parallel_properties))
        p.start()
        active_processes[suburb_name] = p
        print(f"[{suburb_name}] Process started (PID: {p.pid})")
        
        # Stagger starts to avoid WebDriver timeout issues (10 seconds between each)
        if i < min(max_concurrent, len(pending_suburbs) + len(active_processes)) - 1:
            print(f"  Waiting 10 seconds before starting next process...")
            time.sleep(10)
    
    print(f"\n{'='*80}")
    print("MONITORING PROGRESS - DYNAMIC SPAWNING ACTIVE")
    print(f"{'='*80}\n")
    
    # Monitor and spawn new suburbs as others complete
    while active_processes or pending_suburbs:
        # Check for completed processes
        completed_this_round = []
        for suburb_name, process in list(active_processes.items()):
            if not process.is_alive():
                completed_this_round.append(suburb_name)
                completed_suburbs.append(suburb_name)
                del active_processes[suburb_name]
                
                elapsed = time.time() - start_time
                print(f"\n[{suburb_name}] ✅ COMPLETED (Elapsed: {elapsed/60:.1f} mins)")
                print(f"Progress: {len(completed_suburbs)}/{len(suburbs)} suburbs complete")
                print(f"Active: {len(active_processes)}, Pending: {len(pending_suburbs)}\n")
                
                # Spawn new suburb if available
                if pending_suburbs:
                    new_suburb_name, new_postcode = pending_suburbs.pop(0)
                    p = Process(target=run_suburb_scraper, args=(new_suburb_name, new_postcode, progress_queue, parallel_properties))
                    p.start()
                    active_processes[new_suburb_name] = p
                    print(f"[{new_suburb_name}] 🚀 SPAWNED (PID: {p.pid})")
                    print(f"Active: {len(active_processes)}, Pending: {len(pending_suburbs)}\n")
        
        # Process progress updates
        try:
            while not progress_queue.empty():
                progress = progress_queue.get_nowait()
                suburb = progress['suburb']
                status = progress['status']
                data = progress.get('data', {})
                
                # Store results
                if suburb not in results_dict:
                    results_dict[suburb] = {}
                results_dict[suburb][status] = data
                
                # Print progress
                if status == 'discovery_complete':
                    print(f"[{suburb}] Discovery: {data.get('discovered_urls', 0)} URLs found")
                elif status == 'scraping_progress':
                    completed = data.get('completed', 0)
                    total = data.get('total', 0)
                    successful = data.get('successful', 0)
                    if completed % 10 == 0 or completed == total:  # Print every 10 properties
                        print(f"[{suburb}] Progress: {completed}/{total} ({successful} successful)")
        except:
            pass
        
        # Sleep before next check
        time.sleep(10)
    
    # Wait for all processes to complete
    print(f"\n{'='*80}")
    print("WAITING FOR FINAL PROCESSES TO COMPLETE...")
    print(f"{'='*80}\n")

    # Drain any remaining progress updates from the queue
    time.sleep(2)  # Brief wait for final events to arrive
    try:
        while not progress_queue.empty():
            progress = progress_queue.get_nowait()
            suburb = progress['suburb']
            status = progress['status']
            data = progress.get('data', {})
            if suburb not in results_dict:
                results_dict[suburb] = {}
            results_dict[suburb][status] = data
    except:
        pass

    # Final Summary
    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("DYNAMIC SCRAPING COMPLETE - FINAL SUMMARY")
    print("=" * 80)
    print(f"\nTotal Time: {total_time/60:.1f} minutes")
    print(f"Suburbs Processed: {len(completed_suburbs)}/{len(suburbs)}")
    print(f"Average Time per Suburb: {total_time/len(completed_suburbs)/60:.1f} minutes\n")
    
    for suburb_name, postcode in suburbs:
        print(f"📊 {suburb_name.upper()}")
        if suburb_name in results_dict:
            suburb_results = results_dict[suburb_name]
            
            if 'complete' in suburb_results:
                complete_data = suburb_results['complete']
                discovery = complete_data.get('discovery', {})
                scraping = complete_data.get('scraping', {})
                
                print(f"  Expected:    {discovery.get('expected_count', 'N/A')}")
                print(f"  Discovered:  {len(discovery.get('discovered_urls', []))}")
                print(f"  Successful:  {scraping.get('successful', 0)}")
                print(f"  Failed:      {scraping.get('failed', 0)}")
                print(f"  Final Count: {complete_data.get('final_count', 0)} documents in MongoDB")
            elif 'error' in suburb_results:
                print(f"  ❌ Error: {suburb_results['error'].get('error', 'Unknown')}")
            else:
                print(f"  ⚠️ Incomplete")
        else:
            print(f"  ⚠️ No results")
        print()
    
    print("=" * 80 + "\n")

    # Self-healing: Clean up any zombie Chrome processes
    cleanup_zombie_chrome_processes()

    return results_dict


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Dynamic suburb scraping with parallel properties",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--test', action='store_true',
                       help='Test with first 10 suburbs')
    parser.add_argument('--all', action='store_true',
                       help='Process all 52 suburbs')
    parser.add_argument('--suburbs', type=str, default=None,
                       help='Comma-separated list of suburb names to scrape (e.g. "Robina,Varsity Lakes,Burleigh Waters")')
    parser.add_argument('--max-concurrent', type=int, default=5,
                       help='Maximum concurrent suburbs (default: 5)')
    parser.add_argument('--parallel-properties', type=int, default=3,
                       help='Properties to scrape simultaneously per suburb (default: 3)')

    args = parser.parse_args()

    # Load suburbs
    all_suburbs = load_suburbs_from_json()

    if args.suburbs:
        # Filter to only the specified suburbs
        requested = [s.strip() for s in args.suburbs.split(',')]
        requested_lower = [s.lower() for s in requested]
        suburbs = [(name, pc) for name, pc in all_suburbs if name.lower() in requested_lower]
        not_found = [s for s in requested if s.lower() not in [n.lower() for n, _ in all_suburbs]]
        if not_found:
            print(f"\n⚠️ Suburbs not found in config: {', '.join(not_found)}", flush=True)
        if not suburbs:
            print("\n❌ No matching suburbs found", flush=True)
            return 1
        print(f"\n🎯 TARGET MODE: Processing {len(suburbs)} suburbs: {', '.join(n for n,_ in suburbs)}", flush=True)
    elif args.test:
        suburbs = all_suburbs[:10]
        print(f"\n🧪 TEST MODE: Processing first 10 suburbs")
    elif args.all:
        suburbs = all_suburbs
        print(f"\n🚀 PRODUCTION MODE: Processing all {len(suburbs)} suburbs")
    else:
        print("\nPlease specify --test, --all, or --suburbs")
        parser.print_help()
        return 1
    
    # Run dynamic scraping
    results = run_dynamic_scraping(
        suburbs=suburbs,
        max_concurrent=args.max_concurrent,
        parallel_properties=args.parallel_properties
    )
    
    return 0


if __name__ == "__main__":
    exit(main())
