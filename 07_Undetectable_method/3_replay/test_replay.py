#!/usr/bin/env python3
"""
Test Replay Script - Test a single recording replay

This is a simplified test script to verify:
1. Recording file exists and is valid
2. MongoDB connection works
3. Property extraction works
4. Data can be saved to MongoDB

Use this before running full production replays.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from replay_engine import ReplayEngine


async def test_replay(suburb, session_number):
    """Test replay of a single session"""
    print("\n" + "="*70)
    print("  TEST REPLAY")
    print("="*70)
    print(f"\nTesting replay for: {suburb} - Session {session_number}")
    print("This will:")
    print("1. Verify the recording file exists")
    print("2. Check MongoDB connection")
    print("3. Extract property URLs from the recording")
    print("4. Visit the first property page and extract data")
    print("5. Save test data to MongoDB")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start test...")
    
    try:
        # Create engine
        engine = ReplayEngine(suburb, session_number)
        
        # Check recording exists
        if not engine.recording_file.exists():
            print(f"\n❌ Recording not found: {engine.recording_file}")
            print(f"\nCreate it with:")
            print(f"  python 1_recorder/session_recorder.py --suburb {suburb} --session {session_number}")
            return False
        
        print(f"\n✅ Recording found: {engine.recording_file.name}")
        print(f"   Size: {engine.recording_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Run replay (non-headless so you can see it)
        success = await engine.replay_session(headless=False)
        
        if success and engine.properties_extracted:
            print("\n" + "="*70)
            print("✅ TEST PASSED")
            print("="*70)
            print(f"\nSuccessfully extracted {len(engine.properties_extracted)} properties")
            print("\nNext steps:")
            print("1. Check MongoDB to verify data:")
            print("   mongosh mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/")
            print("   > db.properties_for_sale.find().pretty()")
            print("\n2. If data looks good, run full replay:")
            print(f"   python 3_replay/replay_engine.py --suburb {suburb} --session {session_number}")
            print("\n3. Or replay all sessions with random selection:")
            print(f"   python 3_replay/replay_engine.py --suburb {suburb} --session random")
            return True
        else:
            print("\n" + "="*70)
            print("⚠️  TEST COMPLETED BUT NO DATA EXTRACTED")
            print("="*70)
            print("\nPossible issues:")
            print("1. Recording didn't capture property URLs")
            print("2. Property page structure has changed")
            print("3. Network issues during replay")
            print("\nCheck extraction logs:")
            print(f"   ls -la 4_data/extraction_logs/")
            return False
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test a recording replay",
        epilog="Example: python test_replay.py --suburb robina --session 1"
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
    
    success = await test_replay(args.suburb, args.session)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
