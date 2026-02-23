#!/usr/bin/env python3
"""
Session Recorder for Undetectable Web Scraping

This tool records your manual browsing sessions using Playwright.
The recordings capture all your actions (mouse movements, clicks, scrolls, timing)
which can later be replayed to extract data.

Usage:
    python session_recorder.py --suburb robina --session 1
    python session_recorder.py --suburb mudgeeraba --session 2
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import yaml
import json
from playwright.async_api import async_playwright

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


class SessionRecorder:
    """Records browsing sessions using Playwright tracing"""
    
    def __init__(self, suburb, session_number, config_path="../config.yaml"):
        self.suburb = suburb.lower()
        self.session_number = session_number
        self.config = self._load_config(config_path)
        self.recordings_dir = Path(__file__).parent.parent / "2_recordings"
        self.logs_dir = Path(__file__).parent.parent / "logs"
        
        # Create directories
        self.recordings_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Suburb-specific directory
        self.suburb_dir = self.recordings_dir / self.suburb
        self.suburb_dir.mkdir(exist_ok=True)
        
        # Recording filename
        self.recording_file = self.suburb_dir / f"session_{session_number:02d}.zip"
        
    def _load_config(self, config_path):
        """Load configuration from YAML file"""
        # Get the project root (07_Undetectable_method)
        project_root = Path(__file__).parent.parent
        config_file = project_root / "config.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def get_suburb_url(self):
        """Get the URL for the specified suburb"""
        if self.suburb not in self.config['suburbs']:
            raise ValueError(f"Suburb '{self.suburb}' not found in config.yaml")
        return self.config['suburbs'][self.suburb]['url']
    
    async def record_session(self):
        """Record a browsing session"""
        print("\n" + "="*70)
        print(f"  SESSION RECORDER - {self.suburb.upper()} - Session {self.session_number}")
        print("="*70)
        print(f"\nRecording will be saved to: {self.recording_file}")
        print(f"Suburb URL: {self.get_suburb_url()}")
        print("\nINSTRUCTIONS:")
        print("1. Browser will open with Playwright recording ACTIVE")
        print("2. Navigate to realestate.com.au (or it will load automatically)")
        print("3. Search for the suburb if needed")
        print("4. Browse naturally - scroll through listings")
        print("5. Click on 3 PROPERTIES to view their details")
        print("6. View each property page fully")
        print("7. Use browser back button to return to listings")
        print("8. When finished, CLOSE THE BROWSER to stop recording")
        print("\nTIPS:")
        print("- Browse naturally (don't rush)")
        print("- Scroll up and down occasionally")
        print("- Hover over elements")
        print("- Take your time reading")
        print("- Vary your behavior across different sessions")
        print("\n" + "="*70)
        
        input("\nPress ENTER to start recording...")
        
        async with async_playwright() as p:
            # Launch browser
            print("\n🚀 Launching browser...")
            browser = await p.chromium.launch(
                headless=False,  # Visible browser
                channel="chrome"  # Use actual Chrome
            )
            
            # Create context with tracing enabled
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=None,  # Use default Chrome user agent
                locale='en-AU',
                timezone_id='Australia/Brisbane'
            )
            
            # Start tracing
            print("📹 Starting trace recording...")
            await context.tracing.start(
                screenshots=self.config['recording']['trace_screenshots'],
                snapshots=self.config['recording']['trace_snapshots'],
                sources=self.config['recording']['trace_sources']
            )
            
            # Create page
            page = await context.new_page()
            
            # Navigate to suburb URL
            suburb_url = self.get_suburb_url()
            print(f"🌐 Navigating to: {suburb_url}")
            await page.goto(suburb_url, wait_until='networkidle')
            
            print("\n✅ Recording started!")
            print("📌 The browser is now under YOUR control")
            print("📌 Browse normally, click 3 properties, then CLOSE the browser")
            print("📌 Recording will save automatically when you close the browser\n")
            
            # Wait for user to close the browser
            try:
                # Keep the script running until browser is closed
                while True:
                    await asyncio.sleep(1)
                    # Check if context is still alive
                    try:
                        await page.title()
                    except Exception:
                        # Browser was closed
                        break
            except KeyboardInterrupt:
                print("\n⚠️  Recording interrupted by Ctrl+C")
            
            # Stop tracing and save
            print("\n💾 Saving recording...")
            await context.tracing.stop(path=str(self.recording_file))
            
            # Close browser (if not already closed)
            try:
                await browser.close()
            except Exception:
                pass
        
        # Update metadata
        self._update_metadata()
        
        print("\n✅ Recording saved successfully!")
        print(f"📁 File: {self.recording_file}")
        print(f"📊 Size: {self.recording_file.stat().st_size / 1024 / 1024:.2f} MB")
        print("\n" + "="*70)
        print("✅ SESSION RECORDING COMPLETE!")
        print("="*70)
        print(f"\nNext steps:")
        print(f"1. Record remaining sessions for {self.suburb}")
        print(f"2. Or record sessions for other suburbs")
        print(f"3. Then test replay: python 3_replay/test_replay.py --suburb {self.suburb} --session {self.session_number}")
        print("\n")
    
    def _update_metadata(self):
        """Update metadata.json with recording info"""
        metadata_file = self.recordings_dir / "metadata.json"
        
        # Load existing metadata
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Add this recording
        if self.suburb not in metadata:
            metadata[self.suburb] = {}
        
        session_key = f"session_{self.session_number:02d}"
        metadata[self.suburb][session_key] = {
            "recorded_at": datetime.now().isoformat(),
            "file": str(self.recording_file.name),
            "file_size_mb": round(self.recording_file.stat().st_size / 1024 / 1024, 2),
            "suburb_url": self.get_suburb_url()
        }
        
        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Record a browsing session for undetectable scraping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python session_recorder.py --suburb robina --session 1
  python session_recorder.py --suburb mudgeeraba --session 2
  
This will open a browser where you manually browse and click 3 properties.
The session is recorded and can be replayed later to extract data.
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
        type=int,
        required=True,
        help='Session number (1, 2, 3, etc.)'
    )
    
    args = parser.parse_args()
    
    # Validate session number
    if args.session < 1:
        print("❌ Error: Session number must be 1 or greater")
        sys.exit(1)
    
    try:
        # Create recorder
        recorder = SessionRecorder(args.suburb, args.session)
        
        # Record session
        asyncio.run(recorder.record_session())
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nAvailable suburbs in config.yaml:")
        config_file = Path(__file__).parent.parent / "config.yaml"
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        for suburb in config['suburbs'].keys():
            print(f"  - {suburb}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Recording cancelled by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error during recording: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
