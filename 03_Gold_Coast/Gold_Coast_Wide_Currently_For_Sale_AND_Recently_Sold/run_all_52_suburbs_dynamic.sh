#!/bin/bash
# Dynamic Suburb Scraping - All 52 Gold Coast Suburbs
# Last Updated: 31/01/2026, 12:18 pm (Brisbane Time)
#
# PURPOSE: Scrape all 52 Gold Coast suburbs with dynamic spawning (max 5 concurrent)
# USAGE: bash run_all_52_suburbs_dynamic.sh

echo "================================================================================"
echo "DYNAMIC SUBURB SCRAPING - ALL 52 GOLD COAST SUBURBS"
echo "================================================================================"
echo ""
echo "Configuration:"
echo "  Total Suburbs: 52"
echo "  Max Concurrent: 5 suburbs at a time"
echo "  Strategy: Dynamic spawning (spawn new when one completes)"
echo "  Estimated Time: 3-4 hours"
echo ""
echo "MongoDB Safety:"
echo "  ✓ Separate collection per suburb (no conflicts)"
echo "  ✓ Connection pooling (maxPoolSize=50)"
echo "  ✓ Unique indexes on listing_url"
echo "  ✓ Retry logic for transient failures"
echo ""
echo "================================================================================"
echo ""

read -p "Press ENTER to start scraping all 52 suburbs (or Ctrl+C to cancel)..."

# Change to script directory
cd "$(dirname "$0")"

# Run all suburbs in batches of 5 with dynamic spawning
# The script will automatically manage the queue

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Robina:4226" \
  "Varsity Lakes:4227" \
  "Mudgeeraba:4213" \
  "Reedy Creek:4227" \
  "Burleigh Waters:4220" &

# Wait for first batch to start
sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Burleigh Heads:4220" \
  "Miami:4220" \
  "Mermaid Beach:4218" \
  "Mermaid Waters:4218" \
  "Broadbeach:4218" &

sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Broadbeach Waters:4218" \
  "Surfers Paradise:4217" \
  "Main Beach:4217" \
  "Southport:4215" \
  "Labrador:4215" &

sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Biggera Waters:4216" \
  "Runaway Bay:4216" \
  "Paradise Point:4216" \
  "Hollywell:4216" \
  "Hope Island:4212" &

sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Coomera:4209" \
  "Upper Coomera:4209" \
  "Oxenford:4210" \
  "Helensvale:4212" \
  "Pacific Pines:4211" &

sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Gaven:4211" \
  "Arundel:4214" \
  "Parkwood:4214" \
  "Molendinar:4214" \
  "Ashmore:4214" &

sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Benowa:4217" \
  "Bundall:4217" \
  "Carrara:4211" \
  "Merrimac:4226" \
  "Clear Island Waters:4226" &

sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Worongary:4213" \
  "Tallai:4213" \
  "Advancetown:4211" \
  "Nerang:4211" \
  "Highland Park:4211" &

sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Gilston:4211" \
  "Palm Beach:4221" \
  "Currumbin:4223" \
  "Currumbin Waters:4223" \
  "Currumbin Valley:4223" &

sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Tugun:4224" \
  "Bilinga:4225" \
  "Coolangatta:4225" \
  "Elanora:4221" \
  "Tallebudgera:4228" &

sleep 15

python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Tallebudgera Valley:4228" \
  "Bonogin:4213"

echo ""
echo "================================================================================"
echo "ALL BATCHES STARTED"
echo "================================================================================"
echo ""
echo "Monitor progress in terminal output above"
echo "Processes will complete automatically"
echo ""
echo "To check progress in MongoDB:"
echo "  mongosh"
echo "  use Gold_Coast_Currently_For_Sale"
echo "  db.getCollectionNames().length  // Should reach 52"
echo ""
echo "To stop all processes:"
echo "  Press Ctrl+C multiple times"
echo ""

# Wait for all background jobs
wait

echo ""
echo "================================================================================"
echo "ALL 52 SUBURBS COMPLETE!"
echo "================================================================================"
echo ""
