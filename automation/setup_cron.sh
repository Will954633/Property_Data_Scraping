#!/bin/bash
#
# Setup Cron Jobs for Property Scraping Automation
# Schedules daily and bi-daily scraping tasks
#

echo "======================================================================"
echo "CRON JOB SETUP FOR PROPERTY SCRAPING"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  1. Create logs directory"
echo "  2. Add cron jobs for daily and bi-daily scraping"
echo "  3. Show you the crontab entries"
echo ""
echo "Schedules:"
echo "  • Daily at 2:00 AM: Run daily_scraper.py (Script A + DB update)"
echo "  • Every 2 days at 3:00 AM: Run bi_daily_details.py (Script B + change detection)"
echo ""
echo "======================================================================"
echo ""

# Create logs dir
mkdir -p logs
echo "✓ Created logs directory"

# Define cron entries
DAILY_CRON="0 2 * * * cd /Users/projects/Documents/Property_Data_Scraping/automation && /Users/projects/miniconda3/bin/python daily_scraper.py >> logs/cron_daily.log 2>&1"
BI_DAILY_CRON="0 3 */2 * * cd /Users/projects/Documents/Property_Data_Scraping/automation && /Users/projects/miniconda3/bin/python bi_daily_details.py >> logs/cron_bi_daily.log 2>&1"

# Check if cron jobs already exist
if crontab -l 2>/dev/null | grep -q "daily_scraper.py"; then
    echo "⚠ Daily cron job already exists, skipping"
else
    echo "→ Adding daily cron job: $DAILY_CRON"
    (crontab -l 2>/dev/null; echo "$DAILY_CRON") | crontab -
fi

if crontab -l 2>/dev/null | grep -q "bi_daily_details.py"; then
    echo "⚠ Bi-daily cron job already exists, skipping"
else
    echo "→ Adding bi-daily cron job: $BI_DAILY_CRON"
    (crontab -l 2>/dev/null; echo "$BI_DAILY_CRON") | crontab -
fi

echo ""
echo "======================================================================"
echo "CRON SETUP COMPLETE!"
echo "======================================================================"
echo ""
echo "Current crontab entries:"
echo "----------------------------------------------------------------------"
crontab -l 2>/dev/null || echo "No crontab entries found"

echo ""
echo "Next steps:"
echo "  1. Run initial population: cd automation && python daily_scraper.py"
echo "  2. Verify permissions: ./setup_permissions.sh"
echo "  3. Monitor logs: tail -f logs/daily_scraper.log"
echo "  4. Test bi-daily: python bi_daily_details.py"
echo ""
echo "To edit crontab manually: crontab -e"
echo "To list: crontab -l"
echo "To remove: crontab -r"
echo ""
echo "Note: Cron uses system Python path. If issues, edit the Python path in the cron entries."
echo ""
echo "======================================================================"
