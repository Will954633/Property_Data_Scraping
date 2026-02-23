#!/bin/bash
# Monitor Gold Coast Database Update Progress
# Last Updated: 30/01/2026, 7:39 pm (Brisbane Time)

echo "========================================================================"
echo "GOLD COAST DATABASE UPDATE - PROGRESS MONITOR"
echo "========================================================================"
echo ""

# MongoDB connection
MONGO_URI=${MONGODB_URI:-"mongodb://127.0.0.1:27017/"}
DB_NAME="Gold_Coast"

# Function to count documents with scraped_data
count_scraped() {
    mongosh "$MONGO_URI$DB_NAME" --quiet --eval "
        let total = 0;
        db.getCollectionNames().forEach(function(collName) {
            if (collName !== 'system.indexes') {
                let count = db[collName].countDocuments({'scraped_data': {\$exists: true}});
                total += count;
            }
        });
        print(total);
    "
}

# Function to count documents with valuation_history
count_with_history() {
    mongosh "$MONGO_URI$DB_NAME" --quiet --eval "
        let total = 0;
        db.getCollectionNames().forEach(function(collName) {
            if (collName !== 'system.indexes') {
                let count = db[collName].countDocuments({'scraped_data.valuation_history': {\$exists: true}});
                total += count;
            }
        });
        print(total);
    "
}

# Function to get most recent update timestamp
get_latest_update() {
    mongosh "$MONGO_URI$DB_NAME" --quiet --eval "
        let latest = null;
        db.getCollectionNames().forEach(function(collName) {
            if (collName !== 'system.indexes') {
                let doc = db[collName].findOne(
                    {'updated_at': {\$exists: true}},
                    {sort: {'updated_at': -1}, projection: {'updated_at': 1}}
                );
                if (doc && doc.updated_at) {
                    if (!latest || doc.updated_at > latest) {
                        latest = doc.updated_at;
                    }
                }
            }
        });
        if (latest) {
            print(latest.toISOString());
        } else {
            print('No updates yet');
        }
    "
}

# Main monitoring loop
while true; do
    clear
    echo "========================================================================"
    echo "GOLD COAST DATABASE UPDATE - PROGRESS MONITOR"
    echo "========================================================================"
    echo ""
    echo "Checking database status..."
    echo ""
    
    TOTAL_SCRAPED=$(count_scraped)
    TOTAL_WITH_HISTORY=$(count_with_history)
    LATEST_UPDATE=$(get_latest_update)
    
    echo "📊 DATABASE STATISTICS"
    echo "────────────────────────────────────────────────────────────────────────"
    echo "  Total properties with scraped_data:    $TOTAL_SCRAPED"
    echo "  Properties with valuation history:     $TOTAL_WITH_HISTORY"
    echo "  Properties updated (have history):     $(echo "scale=2; $TOTAL_WITH_HISTORY / $TOTAL_SCRAPED * 100" | bc)%"
    echo "  Latest update timestamp:                $LATEST_UPDATE"
    echo "────────────────────────────────────────────────────────────────────────"
    echo ""
    
    # Show per-suburb breakdown
    echo "📍 PER-SUBURB BREAKDOWN (Top 10)"
    echo "────────────────────────────────────────────────────────────────────────"
    mongosh "$MONGO_URI$DB_NAME" --quiet --eval "
        let results = [];
        db.getCollectionNames().forEach(function(collName) {
            if (collName !== 'system.indexes') {
                let total = db[collName].countDocuments({'scraped_data': {\$exists: true}});
                let withHistory = db[collName].countDocuments({'scraped_data.valuation_history': {\$exists: true}});
                if (total > 0) {
                    results.push({
                        suburb: collName,
                        total: total,
                        updated: withHistory,
                        percent: (withHistory / total * 100).toFixed(1)
                    });
                }
            }
        });
        results.sort((a, b) => b.total - a.total);
        results.slice(0, 10).forEach(r => {
            print('  ' + r.suburb.padEnd(30) + ': ' + 
                  r.updated.toString().padStart(6) + ' / ' + 
                  r.total.toString().padStart(6) + ' (' + 
                  r.percent.padStart(5) + '%)');
        });
    "
    echo "────────────────────────────────────────────────────────────────────────"
    echo ""
    echo "Last updated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Refreshing in 30 seconds... (Ctrl+C to exit)"
    echo ""
    
    sleep 30
done
