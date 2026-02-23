# macOS Permissions Fix for Mouse Recording

## ⚠️ Problem

The mouse recorder runs but captures 0 actions because macOS blocks apps from monitoring keyboard/mouse without permission.

---

## ✅ Solution: Grant Accessibility Permissions

### Step 1: Open System Settings

```bash
# Open System Settings directly to Privacy & Security
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
```

**Or manually:**
1. Open **System Settings**
2. Click **Privacy & Security**
3. Click **Accessibility**

---

### Step 2: Grant Permission to Terminal/iTerm

You need to grant permission to whatever app is running the Python script:

**If using Terminal:**
- Look for "Terminal.app" in the list
- Toggle the switch to **ON**

**If using iTerm:**
- Look for "iTerm.app" in the list
- Toggle the switch to **ON**

**If using VS Code Terminal:**
- Look for "Code.app" or "Visual Studio Code"
- Toggle the switch to **ON**

**If not in list:**
- Click the **+** button
- Navigate to Applications
- Add Terminal/iTerm/VS Code

---

### Step 3: Restart Your Terminal

After granting permissions:
1. **Quit** your terminal app completely (Cmd+Q)
2. **Reopen** it
3. Navigate back to the project:
   ```bash
   cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method
   ```

---

### Step 4: Test Again

```bash
# Delete the empty recording
rm 2_recordings/robina/session_01_actions.json

# Try recording again
python 1_recorder/mouse_action_recorder.py --suburb robina --session 1

# Press ENTER to start
# Move your mouse and click a few times
# Press ESC to stop

# You should see messages like:
# "📍 Click recorded at (450, 300) - Button.left"
```

**If you see click messages, it's working!** ✅

---

## 🧪 Quick Test Without Full Recording

Create this test script:

```bash
cat > test_permissions.py << 'EOF'
from pynput import mouse, keyboard
import time

print("Testing mouse/keyboard monitoring...")
print("Move mouse and click - should see position printed")
print("Press ESC to stop")

def on_click(x, y, button, pressed):
    if pressed:
        print(f"✓ Click at ({x}, {y})")

def on_key(key):
    print(f"✓ Key pressed: {key}")
    if key == keyboard.Key.esc:
        return False

# Start listeners
mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener = keyboard.Listener(on_press=on_key)

mouse_listener.start()
keyboard_listener.start()

keyboard_listener.join()
print("\nTest complete!")
EOF

python test_permissions.py
```

**If this works (prints clicks/keys), then the recorder will work!**

---

## 🔧 Alternative: Use AppleScript Instead

If permissions don't work, we can use AppleScript which doesn't require accessibility permissions:

```applescript
-- Opens Chrome and navigates  
tell application "Google Chrome"
    activate
    open location "https://www.realestate.com.au/..."
end tell
```

Combined with screenshot-only approach (no mouse recording needed).

---

## 📝 Summary

**Issue:** pynput can't monitor mouse/keyboard without permissions  
**Fix:** Grant Accessibility permissions to your Terminal app  
**Test:** Run `test_permissions.py` to verify  
**Then:** Re-record your session  

Let me know once you've granted permissions and we can test again!
