#!/usr/bin/env python3
"""
Selenium-based Click Workflow - Works with Selenium-launched Chrome
Uses Selenium's native click capabilities instead of AppleScript
"""

import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class SeleniumClickWorkflow:
    """Complete workflow using Selenium's native clicking"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
    
    def setup_driver(self):
        """Set up Chrome WebDriver"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Undetectable options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        prefs = {"profile.default_content_setting_values.notifications": 2}
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver initialized")
    
    def google_search(self, address, wait_time=3):
        """Perform Google search"""
        try:
            print(f"🔍 Searching Google for: {address}")
            
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Accept cookies
            try:
                accept_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept') or contains(., 'I agree')]"))
                )
                accept_button.click()
                time.sleep(1)
            except:
                pass
            
            # Search
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(address)
            search_box.send_keys(Keys.RETURN)
            
            print(f"⏳ Waiting {wait_time} seconds for results...")
            time.sleep(wait_time)
            
            print("✅ Search completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during search: {str(e)}")
            return False
    
    def click_realestate_result(self, search_text="realestate.com.au", wait_after=3):
        """
        Click the result using Selenium (more reliable than AppleScript)
        """
        try:
            print(f"🖱️  Looking for result containing: {search_text}")
            
            # Try multiple selectors for Google results
            selectors = [
                f"//a[contains(@href, 'realestate.com.au')]//h3",  # Direct h3 in link
                f"//h3[contains(text(), '{search_text}')]",  # H3 containing text
                f"//a[contains(@href, 'realestate.com.au')]",  # Just the link
                "//div[@id='search']//a[contains(@href, 'realestate.com.au')]",  # Link in search results
            ]
            
            element = None
            for selector in selectors:
                try:
                    # Find all matching elements
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    # Filter by text if needed
                    for elem in elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                element = elem
                                break
                        except:
                            continue
                    
                    if element:
                        break
                        
                except Exception as e:
                    continue
            
            if not element:
                print(f"❌ Could not find result containing '{search_text}'")
                return False
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(0.5)
            
            # Try to click
            try:
                element.click()
            except Exception:
                # If regular click fails, use JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
            
            print(f"✅ Clicked on result")
            
            if wait_after > 0:
                print(f"⏳ Waiting {wait_after} seconds for page to load...")
                time.sleep(wait_after)
            
            return True
            
        except Exception as e:
            print(f"❌ Error clicking result: {str(e)}")
            return False
    
    def get_current_url(self):
        """Get current URL"""
        if self.driver:
            return self.driver.current_url
        return None
    
    def close(self):
        """Close browser"""
        if self.driver:
            print("🔒 Closing browser...")
            self.driver.quit()
            self.driver = None
    
    def run_full_workflow(self, address):
        """Run complete workflow"""
        try:
            print("\n" + "=" * 60)
            print("STEP 1: Setting up Chrome browser")
            print("=" * 60)
            self.setup_driver()
            
            print("\n" + "=" * 60)
            print("STEP 2: Performing Google search")
            print("=" * 60)
            if not self.google_search(address):
                return None
            
            print("\n" + "=" * 60)
            print("STEP 3: Clicking realestate.com.au result")
            print("=" * 60)
            if not self.click_realestate_result():
                return None
            
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


def main():
    """Main function"""
    
    print("=" * 60)
    print("SELENIUM CLICK WORKFLOW")
    print("Google Search -> Click Result -> Get Property URL")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} '<address>'")
        print()
        print("Example:")
        print(f"  {sys.argv[0]} '279 Ron Penhaligon Way, Robina'")
        print()
        return 1
    
    address = sys.argv[1]
    print(f"Property Address: {address}")
    print()
    
    workflow = None
    
    try:
        workflow = SeleniumClickWorkflow(headless=False)
        final_url = workflow.run_full_workflow(address)
        
        if final_url:
            print("\n" + "=" * 60)
            print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"Final URL: {final_url}")
            print()
            
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
