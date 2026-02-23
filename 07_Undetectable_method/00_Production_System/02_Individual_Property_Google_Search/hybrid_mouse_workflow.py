#!/usr/bin/env python3
"""
Hybrid Mouse Click Workflow - Uses Selenium for navigation + PyAutoGUI for physical clicks
This avoids Selenium detection by using real mouse movements
"""

import time
import sys
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class HybridMouseWorkflow:
    """Uses Selenium to navigate but PyAutoGUI for clicking"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        # Set PyAutoGUI safety
        pyautogui.PAUSE = 0.5
        pyautogui.FAILSAFE = True
    
    def setup_driver(self):
        """Set up Chrome WebDriver"""
        options = Options()
        
        if self.headless:
            print("⚠️  Warning: Headless mode doesn't work with physical mouse clicks")
            options.add_argument('--headless')
        
        # Undetectable options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        prefs = {"profile.default_content_setting_values.notifications": 2}
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        
        # Maximize window with retry
        self.driver.maximize_window()
        time.sleep(1)  # Wait for maximize to complete
        
        # Force maximize using JavaScript if needed
        self.driver.execute_script("window.moveTo(0, 0); window.resizeTo(screen.width, screen.height);")
        time.sleep(0.5)
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver initialized and maximized")
    
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
    
    def get_element_screen_coordinates(self, search_text="realestate.com.au"):
        """
        Get screen coordinates of a link containing the search text using JavaScript
        Returns (x, y) tuple or None
        """
        try:
            # Escape single quotes in search text
            search_text_escaped = search_text.replace("'", "\\'")
            
            # First, get debugging info
            debug_js = f"""
            (function () {{
                var TARGET_TEXT = '{search_text_escaped}';
                var debug = {{
                    targetText: TARGET_TEXT,
                    h3Count: document.querySelectorAll('a h3').length,
                    linkCount: document.querySelectorAll('a').length,
                    firstFewTexts: []
                }};
                
                // Get first 10 link texts for debugging
                var links = Array.from(document.querySelectorAll('a'));
                for (var i = 0; i < Math.min(10, links.length); i++) {{
                    var text = (links[i].innerText || links[i].textContent || '').substring(0, 100);
                    debug.firstFewTexts.push(text);
                }}
                
                return debug;
            }})();
            """
            
            debug_info = self.driver.execute_script(debug_js)
            print(f"\n🔍 DEBUG INFO:")
            
            if debug_info is None:
                print("   ❌ JavaScript returned None - possible execution error")
                print(f"   Searching for: '{search_text}'")
            else:
                print(f"   Searching for: '{debug_info.get('targetText', 'N/A')}'")
                print(f"   Found {debug_info.get('h3Count', 0)} <h3> elements")
                print(f"   Found {debug_info.get('linkCount', 0)} total links")
                print(f"   First few link texts:")
                for idx, text in enumerate(debug_info.get('firstFewTexts', []), 1):
                    print(f"      {idx}. {text[:80]}...")
            print()
            
            # Now try to find the element
            js_code = f"""
            (function () {{
                var TARGET_TEXT = '{search_text_escaped}';
                
                // Try multiple selectors to find the result
                var selectors = [
                    'a h3',           // Standard h3 titles
                    'a',              // All links
                    '[role="link"]'   // Links with role attribute
                ];
                
                var link = null;
                var foundInfo = {{found: false, selector: '', text: ''}};
                
                // Search through all possible selectors
                for (var i = 0; i < selectors.length; i++) {{
                    var elements = Array.from(document.querySelectorAll(selectors[i]));
                    
                    for (var j = 0; j < elements.length; j++) {{
                        var elem = elements[j];
                        var text = elem.innerText || elem.textContent || '';
                        
                        if (text.toLowerCase().includes(TARGET_TEXT.toLowerCase())) {{
                            foundInfo.found = true;
                            foundInfo.selector = selectors[i];
                            foundInfo.text = text.substring(0, 100);
                            
                            // If it's not an <a> tag, find the closest parent <a>
                            if (elem.tagName.toLowerCase() === 'a') {{
                                link = elem;
                            }} else {{
                                link = elem.closest('a');
                            }}
                            
                            if (link) {{
                                // Make sure the link is visible
                                var rect = link.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0 && rect.top >= 0) {{
                                    foundInfo.visible = true;
                                    break;
                                }} else {{
                                    foundInfo.visible = false;
                                    link = null;
                                }}
                            }}
                        }}
                    }}
                    
                    if (link) break;
                }}
                
                if (!link) return {{found: foundInfo.found, info: foundInfo}};
                
                var rect = link.getBoundingClientRect();
                var winX = window.screenX;
                var winY = window.screenY;
                var chromeHeight = window.outerHeight - window.innerHeight;
                
                var x = Math.round(winX + rect.left + rect.width / 2);
                var y = Math.round(winY + chromeHeight + rect.top + rect.height / 2);
                
                return {{x: x, y: y, found: true, info: foundInfo}};
            }})();
            """
            
            result = self.driver.execute_script(js_code)
            
            if result:
                if result.get('found'):
                    info = result.get('info', {})
                    print(f"✅ Match found!")
                    print(f"   Selector: {info.get('selector', 'N/A')}")
                    print(f"   Text: {info.get('text', 'N/A')[:100]}")
                    print(f"   Visible: {info.get('visible', 'N/A')}")
                
                if 'x' in result and 'y' in result:
                    return (result['x'], result['y'])
                else:
                    print(f"⚠️  Text found but element not clickable/visible")
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting coordinates: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def click_with_mouse(self, x, y):
        """Use cliclick (pure macOS native) for completely undetectable clicks"""
        try:
            import subprocess
            import random
            
            print(f"🖱️  Moving mouse to ({x}, {y})")
            
            # Add slight random offset for more human-like behavior (±3 pixels)
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            final_x = x + offset_x
            final_y = y + offset_y
            
            print(f"🖱️  Using cliclick (native macOS) to click at ({final_x}, {final_y})")
            
            # Use cliclick for 100% native macOS click - completely undetectable
            # Format: "c:x,y" for click at coordinates
            click_command = ["cliclick", f"c:{final_x},{final_y}"]
            
            result = subprocess.run(
                click_command,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"✅ Native macOS click successful!")
                return True
            else:
                print(f"❌ cliclick error: {result.stderr}")
                return False
            
        except subprocess.TimeoutExpired:
            print(f"❌ cliclick command timed out")
            return False
        except FileNotFoundError:
            print(f"❌ cliclick not found - make sure it's installed: brew install cliclick")
            return False
        except Exception as e:
            print(f"❌ Error clicking: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def click_address_result(self, address, wait_after=3):
        """
        Find and click the first result - try multiple search strategies
        """
        try:
            # Strategy 1: Try full address
            print(f"🔍 Strategy 1: Looking for full address: '{address}'")
            coords = self.get_element_screen_coordinates(address)
            
            if not coords:
                # Strategy 2: Try just "realestate" (more likely to work)
                print(f"⚠️  Strategy 1 failed, trying Strategy 2: 'realestate.com.au'")
                coords = self.get_element_screen_coordinates("realestate.com.au")
            
            if not coords:
                # Strategy 3: Try using Selenium to find and get position
                print(f"⚠️  Strategy 2 failed, trying Strategy 3: Selenium element location")
                try:
                    # Find element using Selenium
                    from selenium.webdriver.common.by import By
                    elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'realestate.com.au')]")
                    if elements:
                        elem = elements[0]
                        # Scroll into view
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                        time.sleep(0.5)
                        
                        # Get element location and size
                        location = elem.location
                        size = elem.size
                        
                        # Calculate screen coordinates
                        # Note: location is relative to page, we need screen coordinates
                        viewport_x = self.driver.execute_script("return window.screenX;")
                        viewport_y = self.driver.execute_script("return window.screenY;")
                        chrome_height = self.driver.execute_script("return window.outerHeight - window.innerHeight;")
                        
                        x = viewport_x + location['x'] + size['width'] // 2
                        y = viewport_y + chrome_height + location['y'] + size['height'] // 2
                        
                        coords = (x, y)
                        print(f"✅ Found using Selenium!")
                except Exception as e:
                    print(f"   Strategy 3 also failed: {e}")
            
            if not coords:
                print(f"❌ All strategies failed - could not find clickable element")
                return False
            
            x, y = coords
            print(f"📍 Found element at screen coordinates: ({x}, {y})")
            
            # Click using physical mouse movement
            if not self.click_with_mouse(x, y):
                return False
            
            if wait_after > 0:
                print(f"⏳ Waiting {wait_after} seconds for page to load...")
                time.sleep(wait_after)
            
            return True
            
        except Exception as e:
            print(f"❌ Error in click workflow: {str(e)}")
            import traceback
            traceback.print_exc()
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
            print("STEP 3: Clicking address result with PHYSICAL mouse")
            print("=" * 60)
            if not self.click_address_result(address):
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
    print("HYBRID MOUSE CLICK WORKFLOW")
    print("Selenium Navigation + PyAutoGUI Physical Mouse Clicks")
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
    print("⚠️  IMPORTANT: Do not move your mouse during the clicking phase!")
    print()
    
    workflow = None
    
    try:
        workflow = HybridMouseWorkflow(headless=False)
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
