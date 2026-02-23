#!/usr/bin/env python3
"""
Complete CLI Click Workflow - Full automation for Google search to realestate.com.au
This combines Google search with the reliable cliclick method for clicking results.
"""

import subprocess
import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class CompleteCliClickWorkflow:
    """Complete workflow for searching Google and clicking realestate.com.au results"""
    
    def __init__(self, headless=False):
        """
        Initialize the workflow
        
        Args:
            headless (bool): Whether to run Chrome in headless mode (not recommended for cliclick)
        """
        self.script_dir = Path(__file__).parent
        self.click_script = self.script_dir / "click_google_result.sh"
        self.headless = headless
        self.driver = None
        
        # Verify click script exists
        if not self.click_script.exists():
            raise FileNotFoundError(f"Click script not found at: {self.click_script}")
        
        if not self.click_script.stat().st_mode & 0o111:
            raise PermissionError(f"Click script is not executable. Run: chmod +x {self.click_script}")
    
    def setup_driver(self):
        """Set up Chrome WebDriver"""
        options = Options()
        
        # Important: Don't run headless for cliclick to work
        if self.headless:
            print("⚠️  Warning: Headless mode may not work with cliclick")
            options.add_argument('--headless')
        
        # Add options for undetectable browsing
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Disable notifications
        prefs = {
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver initialized")
    
    def google_search(self, address, wait_time=3):
        """
        Perform a Google search for an address
        
        Args:
            address (str): The property address to search
            wait_time (float): Time to wait after search
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"🔍 Searching Google for: {address}")
            
            # Navigate to Google
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Accept cookies if present
            try:
                accept_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept') or contains(., 'I agree')]"))
                )
                accept_button.click()
                time.sleep(1)
            except:
                pass  # No cookie banner
            
            # Find search box and enter address
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(address)
            search_box.send_keys(Keys.RETURN)
            
            print(f"⏳ Waiting {wait_time} seconds for results to load...")
            time.sleep(wait_time)
            
            print("✅ Search completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during Google search: {str(e)}")
            return False
    
    def click_realestate_result(self, wait_after=3):
        """
        Click the realestate.com.au result using cliclick method
        
        Args:
            wait_after (float): Time to wait after clicking
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("🖱️  Attempting to click realestate.com.au result...")
            
            # Use the bash script to click
            result = subprocess.run(
                [str(self.click_script), "realestate.com.au"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            print(f"✅ {result.stdout.strip()}")
            
            if wait_after > 0:
                print(f"⏳ Waiting {wait_after} seconds for page to load...")
                time.sleep(wait_after)
            
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            print(f"❌ Error clicking result: {error_msg}")
            return False
            
        except subprocess.TimeoutExpired:
            print("❌ Error: Click script timed out")
            return False
            
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return False
    
    def get_current_url(self):
        """Get the current URL from the browser"""
        if self.driver:
            return self.driver.current_url
        return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            print("🔒 Closing browser...")
            self.driver.quit()
            self.driver = None
    
    def run_full_workflow(self, address):
        """
        Run the complete workflow: search -> click -> get URL
        
        Args:
            address (str): Property address to search
            
        Returns:
            str or None: The final URL if successful, None otherwise
        """
        try:
            # Step 1: Setup driver
            print("\n" + "=" * 60)
            print("STEP 1: Setting up Chrome browser")
            print("=" * 60)
            self.setup_driver()
            
            # Step 2: Google search
            print("\n" + "=" * 60)
            print("STEP 2: Performing Google search")
            print("=" * 60)
            if not self.google_search(address):
                return None
            
            # Step 3: Click result
            print("\n" + "=" * 60)
            print("STEP 3: Clicking realestate.com.au result")
            print("=" * 60)
            if not self.click_realestate_result():
                return None
            
            # Step 4: Get final URL
            print("\n" + "=" * 60)
            print("STEP 4: Getting property page URL")
            print("=" * 60)
            final_url = self.get_current_url()
            
            if final_url:
                print(f"✅ Successfully reached: {final_url}")
                return final_url
            else:
                print("❌ Could not get final URL")
                return None
            
        except Exception as e:
            print(f"❌ Workflow error: {str(e)}")
            return None
        
        finally:
            # Keep browser open for inspection
            print("\n" + "=" * 60)
            print("Browser will remain open for inspection")
            print("Press Ctrl+C to close and exit")
            print("=" * 60)


def main():
    """Main function"""
    
    print("=" * 60)
    print("COMPLETE CLICLICK WORKFLOW")
    print("Google Search -> Click Result -> Get Property URL")
    print("=" * 60)
    print()
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} '<address>'")
        print()
        print("Example:")
        print(f"  {sys.argv[0]} '10 Example Street, Gold Coast QLD 4217'")
        print()
        return 1
    
    address = sys.argv[1]
    print(f"Property Address: {address}")
    print()
    
    workflow = None
    
    try:
        # Run the workflow
        workflow = CompleteCliClickWorkflow(headless=False)
        final_url = workflow.run_full_workflow(address)
        
        if final_url:
            print("\n" + "=" * 60)
            print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"Final URL: {final_url}")
            print()
            
            # Keep browser open
            input("Press Enter to close browser and exit...")
            return 0
        else:
            print("\n" + "=" * 60)
            print("❌ WORKFLOW FAILED")
            print("=" * 60)
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        return 1
    
    finally:
        if workflow:
            workflow.close()


if __name__ == "__main__":
    sys.exit(main())
