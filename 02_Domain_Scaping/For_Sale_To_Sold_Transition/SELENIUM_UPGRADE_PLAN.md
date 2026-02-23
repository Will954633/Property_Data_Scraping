# Sold Property Monitor - Selenium Upgrade Plan

**Date: 27/01/2026, 9:38 AM (Monday) - Brisbane**

## Problem Identified

The sold property monitor uses **simple HTTP requests** (`requests` library), while all other scrapers use **Selenium with Chrome WebDriver**. This is causing:

1. **Bot detection issues** - Domain.com.au blocks simple HTTP requests
2. **JavaScript rendering problems** - Sold indicators may be client-side rendered
3. **Network timeouts** - Requests are being blocked/rejected

## Evidence

### Other Scrapers (Working)
```python
# property_detail_scraper_forsale.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(url)
html = driver.page_source  # Full rendered HTML
```

### Sold Monitor (Not Working)
```python
# sold_property_monitor.py
import requests

response = requests.get(url, headers=self.headers, timeout=15)
html = response.text  # Raw HTML, no JavaScript rendering
```

## Solution: Upgrade to Selenium

### Benefits
1. ✅ **Avoids bot detection** - Real browser, not HTTP client
2. ✅ **Renders JavaScript** - Gets fully rendered HTML
3. ✅ **Matches other scrapers** - Consistent approach across all scripts
4. ✅ **No additional cost** - Uses existing Selenium setup
5. ✅ **Proven to work** - Other scrapers successfully use this method

### Implementation Plan

#### 1. Update `sold_property_monitor.py`
- Replace `requests` library with Selenium WebDriver
- Add browser initialization and cleanup
- Update `fetch_listing_html()` to use Selenium
- Add proper wait times for page loading
- Reuse Chrome options from other scrapers

#### 2. Update `requirements.txt`
```txt
requests>=2.31.0  # Remove or keep for other uses
beautifulsoup4>=4.12.0
pymongo>=4.6.0
selenium>=4.15.0  # Add
webdriver-manager>=4.0.0  # Add
```

#### 3. Update Shell Script
- No changes needed - still runs Python script

#### 4. Test with Selenium
- Should work immediately like other scrapers
- No network timeouts
- Full HTML rendering

## Alternative: Bright Data (Not Recommended Yet)

### When to Consider Bright Data
- **After** Selenium upgrade if still having issues
- If Domain.com.au implements aggressive IP-based blocking
- If need to scale to thousands of requests per hour

### Why Not Now
1. Other scrapers work fine with Selenium (no Bright Data)
2. Adds monthly cost ($500+/month for residential proxies)
3. Adds complexity (proxy rotation, authentication)
4. Selenium should solve the current problem

## Recommendation

**Upgrade to Selenium First** - This matches what the working scrapers do and should solve the bot detection issue without additional cost or complexity.

If Selenium still has issues, THEN consider Bright Data as a fallback.

## Next Steps

1. ✅ Identified root cause (simple requests vs Selenium)
2. [ ] Implement Selenium-based version
3. [ ] Test with real properties
4. [ ] Deploy if successful
5. [ ] Monitor next orchestrator run
6. [ ] Only consider Bright Data if Selenium fails

---

**The issue is NOT network connectivity - it's bot detection blocking simple HTTP requests. Selenium will solve this.**
