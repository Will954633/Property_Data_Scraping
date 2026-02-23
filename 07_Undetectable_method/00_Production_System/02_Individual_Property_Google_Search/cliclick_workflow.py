#!/usr/bin/env python3
"""
CLI Click Workflow - Reliably click Google search results using AppleScript + cliclick
This script integrates the click_google_result.sh bash script into a Python workflow.
"""

import subprocess
import time
import sys
from pathlib import Path

class CliClickGoogleClicker:
    """Handles clicking Google search results using the cliclick method"""
    
    def __init__(self):
        # Get the script directory
        self.script_dir = Path(__file__).parent
        self.click_script = self.script_dir / "click_google_result.sh"
        
        # Verify the script exists
        if not self.click_script.exists():
            raise FileNotFoundError(f"Click script not found at: {self.click_script}")
        
        # Verify the script is executable
        if not self.click_script.stat().st_mode & 0o111:
            raise PermissionError(f"Click script is not executable. Run: chmod +x {self.click_script}")
    
    def click_result(self, title_text, verbose=True):
        """
        Click a Google search result by title text
        
        Args:
            title_text (str): Partial text to match in the result title
            verbose (bool): Whether to print progress messages
            
        Returns:
            bool: True if successful, False otherwise
        """
        if verbose:
            print(f"🔍 Searching for result containing: '{title_text}'")
        
        try:
            result = subprocess.run(
                [str(self.click_script), title_text],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            if verbose:
                print(f"✅ {result.stdout.strip()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            if verbose:
                print(f"❌ Error: {error_msg}")
            return False
            
        except subprocess.TimeoutExpired:
            if verbose:
                print("❌ Error: Script timed out after 10 seconds")
            return False
            
        except Exception as e:
            if verbose:
                print(f"❌ Unexpected error: {str(e)}")
            return False
    
    def click_realestate_result(self, wait_after=2.0, verbose=True):
        """
        Convenience method to click the first realestate.com.au result
        
        Args:
            wait_after (float): Seconds to wait after clicking
            verbose (bool): Whether to print progress messages
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = self.click_result("realestate.com.au", verbose=verbose)
        
        if success and wait_after > 0:
            if verbose:
                print(f"⏳ Waiting {wait_after} seconds for page to load...")
            time.sleep(wait_after)
        
        return success


def main():
    """Main function for testing/demonstration"""
    
    print("=" * 60)
    print("CLI Click Google Result - Python Integration")
    print("=" * 60)
    print()
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} <search_text>")
        print()
        print("Examples:")
        print(f"  {sys.argv[0]} 'realestate.com.au'")
        print(f"  {sys.argv[0]} 'property details'")
        print()
        print("For automatic realestate.com.au clicking:")
        print("  Use the click_realestate_result() method in your code")
        print()
        return 1
    
    search_text = sys.argv[1]
    
    try:
        # Initialize the clicker
        clicker = CliClickGoogleClicker()
        
        # Click the result
        print(f"Attempting to click result with text: '{search_text}'")
        print()
        
        success = clicker.click_result(search_text)
        
        print()
        if success:
            print("✅ Click completed successfully!")
            return 0
        else:
            print("❌ Click failed. See errors above.")
            return 1
            
    except FileNotFoundError as e:
        print(f"❌ {str(e)}")
        return 1
    except PermissionError as e:
        print(f"❌ {str(e)}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
