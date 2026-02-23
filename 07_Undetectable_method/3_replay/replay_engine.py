#!/usr/bin/env python3
"""
Replay Engine - Replays recorded browsing sessions and extracts property data

This engine:
1. Loads a recorded session (Playwright trace)
2. Extracts property URLs from the trace
3. Visits each property page with timing variations
4. Extracts property data
5. Saves to MongoDB

Note: Since Playwright traces are for debugging/viewing only, this engine
extracts the URLs from recordings and re-visits them with human-like timing.
"""

import argparse
import asyncio
import sys
import json
import random
import zipfile
from pathlib import Path
from datetime import datetime
import yaml
from playwright.async_api import async_playwright
from property_extractor import PropertyExtractor
from mongodb_saver import MongoDBSaver

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class ReplayEngine:
    """Replays recorded sessions and extracts property data"""
    
    def __init__(self, suburb, session_number, config_path="../config.yaml"):
        self.suburb = suburb.lower()
        self.session_number = session_number
        self.config = self._load_config(config_path)
        
        # Paths
        self.recordings_dir = Path(__file__).parent.parent / "2_recordings"
        self.logs_dir = Path(__file__).parent.parent / "logs"
        self.data_dir = Path(__file__).parent.parent / "4_data"
        
        # Create directories
        self.logs_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "extraction_logs").mkdir(exist_ok=True)
        
        # Recording file
        self.recording_file = self.recordings_dir / self.suburb / f"session_{session_number:02d}.zip"
        
        # Session ID for tracking
        self.session_id = f"{self.suburb}_session_{session_number:02d}"
        
        # Components
        self.extractor = PropertyExtractor()
        self.saver = None
        
        # Results
        self.properties_extracted = []
        self.property_urls = []
    
    def _load_config(self, config_path):
        """Load configuration"""
        # Get the project root (07_Undetectable_method)
        project_root = Path(__file__).parent.parent
        config_file = project_root / "config.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def extract_property_urls_from_trace(self) -> list:
        """
        Extract property URLs from Playwright trace file
        
        Returns:
            list: Property URLs found in the trace
        """
        print(f"📂 Analyzing trace file: {self.recording_file.name}")
        
        property_urls = []
        
        try:
            with zipfile.ZipFile(self.recording_file, 'r') as trace_zip:
                # Read the trace file (network log)
                if 'trace.network' in trace_zip.namelist():
                    network_data = trace_zip.read('trace.network').decode('utf-8')
                    
                    # Parse URLs from network log
                    for line in network_data.split('\n'):
                        if 'realestate.com.au/property' in line:
                            # Extract URL pattern
                            import re
                            url_match = re.search(r'(https?://[^\s"\'<>]+/property/[^\s"\'<>]+)', line)
                            if url_match:
                                url = url_match.group(1).split('?')[0]  # Remove query params
                                if url not in property_urls:
                                    property_urls.append(url)
        
        except Exception as e:
            print(f"⚠️  Warning: Could not extract URLs from trace: {e}")
            print(f"   Will use manual URL input mode instead")
        
        # If no URLs found in trace, we'll prompt for manual entry
        if not property_urls:
            print("\n⚠️  No property URLs found in trace file")
            print("This could mean:")
            print("1. The trace format has changed")
            print("2. The recording didn't capture the data")
            print("3. You need to provide URLs manually")
            
            # For now, use the suburb URL and we'll detect properties during live browsing
            suburb_url = self.config['suburbs'][self.suburb]['url']
            return [suburb_url]
        
        print(f"✅ Found {len(property_urls)} property URLs in trace")
        for i, url in enumerate(property_urls, 1):
            print(f"   {i}. {url[:80]}...")
        
        return property_urls
    
    async def replay_session(self, headless=True):
        """
        Replay the recorded session by visiting captured URLs
        
        Args:
            headless: Run browser in headless mode
        """
        print("\n" + "="*70)
        print(f"  REPLAY ENGINE - {self.suburb.upper()} - Session {self.session_number}")
        print("="*70)
        
        # Check recording exists
        if not self.recording_file.exists():
            print(f"\n❌ Error: Recording not found: {self.recording_file}")
            print(f"\nPlease create the recording first:")
            print(f"  python 1_recorder/session_recorder.py --suburb {self.suburb} --session {self.session_number}")
            return False
        
        # Extract URLs from trace
        self.property_urls = self.extract_property_urls_from_trace()
        
        if not self.property_urls:
            print("\n❌ Error: No URLs to replay")
            return False
        
        # Connect to MongoDB
        print(f"\n💾 Connecting to MongoDB...")
        self.saver = MongoDBSaver()
        
        # Launch browser
        print(f"\n🚀 Launching browser...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                channel="chrome"
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=None,
                locale='en-AU',
                timezone_id='Australia/Brisbane'
            )
            
            page = await context.new_page()
            
            print(f"\n🔄 Replaying session with timing variations...")
            print(f"   URLs to visit: {len(self.property_urls)}")
            print(f"   Timing variation: ±{int(self.config['replay']['timing_variation']*100)}%")
            
            # Visit each URL and extract data
            for i, url in enumerate(self.property_urls, 1):
                print(f"\n{'='*70}")
                print(f"Property {i}/{len(self.property_urls)}")
                print(f"{'='*70}")
                
                try:
                    # Add random delay before navigation (human-like)
                    delay = self._get_varied_delay()
                    print(f"⏱️  Waiting {delay:.1f}s before navigation...")
                    await asyncio.sleep(delay)
                    
                    # Navigate to property page
                    print(f"🌐 Navigating to: {url[:80]}...")
                    await page.goto(url, wait_until='networkidle', timeout=60000)
                    
                    # Wait for page to be stable (with variation)
                    stability_wait = self._get_varied_delay(2, 4)
                    print(f"⏱️  Waiting {stability_wait:.1f}s for page stability...")
                    await asyncio.sleep(stability_wait)
                    
                    # Scroll page (human-like)
                    print(f"📜 Scrolling page...")
                    await self._human_scroll(page)
                    
                    # Get page HTML
                    html = await page.content()
                    current_url = page.url
                    
                    # Extract property data
                    print(f"📊 Extracting property data...")
                    property_data = self.extractor.extract_from_html(
                        html,
                        current_url,
                        self.suburb,
                        self.session_id
                    )
                    
                    # Validate extraction
                    is_valid, missing = self.extractor.validate_extraction(
                        property_data,
                        self.config['extraction']['validate_required_fields']
                    )
                    
                    if is_valid:
                        print(f"✅ Data extraction successful")
                        print(f"   Address: {property_data['address'].get('full', 'Unknown')}")
                        print(f"   Price: {property_data['price'].get('display', 'Unknown')}")
                        print(f"   Beds: {property_data['features'].get('bedrooms', '?')}, "
                              f"Baths: {property_data['features'].get('bathrooms', '?')}, "
                              f"Parking: {property_data['features'].get('parking', '?')}")
                        
                        # Save to MongoDB
                        if self.saver.save_property(property_data):
                            self.properties_extracted.append(property_data)
                    else:
                        print(f"⚠️  Data extraction incomplete - missing: {missing}")
                        print(f"   Saving anyway with partial data...")
                        if self.saver.save_property(property_data):
                            self.properties_extracted.append(property_data)
                    
                    # Save extraction log
                    self._save_extraction_log(i, property_data, html)
                    
                except Exception as e:
                    print(f"❌ Error processing {url}: {e}")
                    continue
            
            # Close browser
            await browser.close()
        
        # Close MongoDB connection
        self.saver.close()
        
        # Print summary
        self._print_summary()
        
        return True
    
    def _get_varied_delay(self, min_delay=None, max_delay=None):
        """Get a delay with timing variation"""
        if min_delay is None:
            min_delay = self.config['replay']['min_wait']
        if max_delay is None:
            max_delay = self.config['replay']['max_wait']
        
        base_delay = random.uniform(min_delay, max_delay)
        variation = self.config['replay']['timing_variation']
        
        # Add ±variation
        varied_delay = base_delay * random.uniform(1 - variation, 1 + variation)
        
        return varied_delay
    
    async def _human_scroll(self, page):
        """Perform human-like scrolling"""
        # Scroll down in chunks
        scroll_height = await page.evaluate('document.body.scrollHeight')
        current_position = 0
        
        # Scroll 3-4 times with random amounts
        num_scrolls = random.randint(3, 4)
        chunk_size = scroll_height // num_scrolls
        
        for _ in range(num_scrolls):
            scroll_amount = int(chunk_size * random.uniform(0.8, 1.2))
            await page.evaluate(f'window.scrollBy(0, {scroll_amount})')
            current_position += scroll_amount
            
            # Random pause while "reading"
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Sometimes scroll back up
        if random.random() < 0.3:
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(random.uniform(0.5, 1.0))
    
    def _save_extraction_log(self, property_index, property_data, html):
        """Save extraction log for debugging"""
        log_dir = self.data_dir / "extraction_logs"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = log_dir / f"{self.session_id}_property_{property_index}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(property_data, f, indent=2, default=str)
        
        # Save HTML if configured
        if self.config['extraction']['save_html']:
            html_file = log_dir / f"{self.session_id}_property_{property_index}_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html)
    
    def _print_summary(self):
        """Print extraction summary"""
        print("\n" + "="*70)
        print("  REPLAY COMPLETE")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"   Properties visited: {len(self.property_urls)}")
        print(f"   Properties extracted: {len(self.properties_extracted)}")
        print(f"   Success rate: {len(self.properties_extracted)/len(self.property_urls)*100:.1f}%")
        print(f"   Session: {self.session_id}")
        print(f"   Suburb: {self.suburb}")
        
        if self.properties_extracted:
            print(f"\n✅ Extracted Properties:")
            for i, prop in enumerate(self.properties_extracted, 1):
                address = prop['address'].get('full', 'Unknown Address')
                price = prop['price'].get('display', 'Unknown Price')
                print(f"   {i}. {address[:60]} - {price}")
        
        print(f"\n💾 Data saved to MongoDB:")
        print(f"   Database: property_data")
        print(f"   Collection: properties_for_sale")
        
        print(f"\n📁 Extraction logs saved to:")
        print(f"   {self.data_dir / 'extraction_logs'}")
        
        print("\n" + "="*70)


async def main():
    parser = argparse.ArgumentParser(
        description="Replay a recording session and extract property data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python replay_engine.py --suburb robina --session 1
  python replay_engine.py --suburb mudgeeraba --session 2 --headless
  python replay_engine.py --suburb robina --session random
  
This will replay the recorded session, visit property pages,
extract data, and save to MongoDB.
        """
    )
    
    parser.add_argument(
        '--suburb',
        type=str,
        required=True,
        help='Suburb name (e.g., robina, mudgeeraba)'
    )
    
    parser.add_argument(
        '--session',
        type=str,
        required=True,
        help='Session number (1, 2, 3) or "random" to pick randomly'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (default: visible)'
    )
    
    args = parser.parse_args()
    
    # Handle random session selection
    if args.session.lower() == 'random':
        session_number = random.randint(1, 3)
        print(f"🎲 Randomly selected session: {session_number}")
    else:
        try:
            session_number = int(args.session)
        except ValueError:
            print("❌ Error: Session must be a number (1, 2, 3) or 'random'")
            sys.exit(1)
    
    try:
        # Create replay engine
        engine = ReplayEngine(args.suburb, session_number)
        
        # Replay session
        success = await engine.replay_session(headless=args.headless)
        
        if success:
            print("\n✅ Replay completed successfully!")
        else:
            print("\n❌ Replay failed")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Replay interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error during replay: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
