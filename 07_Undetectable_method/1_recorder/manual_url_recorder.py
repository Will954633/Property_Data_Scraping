#!/usr/bin/env python3
"""
Manual URL Recorder - Record property URLs manually

Since automated browsers (Playwright/Selenium) are detected, this tool lets you:
1. Browse normally in YOUR regular browser
2. Copy/paste the property URLs you visit
3. Save them for later automated replay

This is completely undetectable because YOU are doing the browsing manually.
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))


class ManualURLRecorder:
    """Records property URLs manually entered by the user"""
    
    def __init__(self, suburb, session_number):
        self.suburb = suburb.lower()
        self.session_number = session_number
        self.recordings_dir = Path(__file__).parent.parent / "2_recordings"
        
        # Create directories
        self.recordings_dir.mkdir(exist_ok=True)
        self.suburb_dir = self.recordings_dir / self.suburb
        self.suburb_dir.mkdir(exist_ok=True)
        
        # URL list file
        self.url_file = self.suburb_dir / f"session_{session_number:02d}_urls.json"
        
        self.urls = []
    
    def record_urls(self):
        """Interactively record URLs from user"""
        print("\n" + "="*70)
        print(f"  MANUAL URL RECORDER - {self.suburb.upper()} - Session {self.session_number}")
        print("="*70)
        print("\nINSTRUCTIONS:")
        print("1. Open YOUR regular browser (Chrome/Safari/Firefox)")
        print("2. Navigate to realestate.com.au")
        print(f"3. Search for properties in {self.suburb}")
        print("4. Click on 3 different properties")
        print("5. For each property, COPY the URL from your browser's address bar")
        print("6. Come back here and PASTE each URL when prompted")
        print("\n" + "="*70)
        
        input("\nPress ENTER when you're ready to start entering URLs...")
        
        print(f"\n📝 Enter 3 property URLs (one at a time)")
        print("   Copy each URL from your browser and paste it here")
        print("   Press ENTER after each URL")
        print("   Type 'done' when finished\n")
        
        count = 1
        while True:
            try:
                url = input(f"Property {count} URL: ").strip()
                
                if url.lower() == 'done':
                    break
                
                if not url:
                    print("   ⚠️  Empty URL, skipped")
                    continue
                
                # Validate URL
                if 'realestate.com.au' not in url:
                    print("   ⚠️  URL doesn't appear to be from realestate.com.au")
                    retry = input("   Add anyway? (y/n): ").lower()
                    if retry != 'y':
                        continue
                
                # Clean URL (remove query params after first ?)
                clean_url = url.split('?')[0] if '?' in url else url
                
                self.urls.append({
                    'url': clean_url,
                    'original_url': url,
                    'order': count,
                    'captured_at': datetime.now().isoformat()
                })
                
                print(f"   ✅ Added: {clean_url[:70]}...")
                count += 1
                
                if count > 3:
                    print(f"\n✅ Captured 3 URLs! Type 'done' to finish, or add more...")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Recording cancelled")
                return False
        
        if not self.urls:
            print("\n❌ No URLs captured")
            return False
        
        # Save URLs
        self._save_urls()
        
        print("\n" + "="*70)
        print("✅ URL RECORDING COMPLETE!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"   URLs captured: {len(self.urls)}")
        print(f"   Saved to: {self.url_file}")
        
        print(f"\n📋 Captured URLs:")
        for i, entry in enumerate(self.urls, 1):
            print(f"   {i}. {entry['url'][:70]}...")
        
        print(f"\n🚀 Next steps:")
        print(f"1. Record more sessions if needed:")
        print(f"   python 1_recorder/manual_url_recorder.py --suburb {self.suburb} --session {self.session_number + 1}")
        print(f"\n2. Test replay with these URLs:")
        print(f"   python 3_replay/test_replay.py --suburb {self.suburb} --session {self.session_number}")
        print()
        
        return True
    
    def _save_urls(self):
        """Save URLs to JSON file"""
        data = {
            'suburb': self.suburb,
            'session': self.session_number,
            'recorded_at': datetime.now().isoformat(),
            'url_count': len(self.urls),
            'urls': self.urls
        }
        
        with open(self.url_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update metadata
        self._update_metadata()
    
    def _update_metadata(self):
        """Update metadata.json"""
        metadata_file = self.recordings_dir / "metadata.json"
        
        # Load existing
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
            "file": str(self.url_file.name),
            "url_count": len(self.urls),
            "method": "manual_urls"
        }
        
        # Save
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Manually record property URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manual_url_recorder.py --suburb robina --session 1
  python manual_url_recorder.py --suburb mudgeeraba --session 2

This tool lets you browse normally in YOUR browser and manually
enter the property URLs you visit. This is 100% undetectable since
you're doing the browsing manually.
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
    
    if args.session < 1:
        print("❌ Error: Session number must be 1 or greater")
        sys.exit(1)
    
    try:
        recorder = ManualURLRecorder(args.suburb, args.session)
        
        success = recorder.record_urls()
        
        if not success:
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Recording cancelled")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
