# SikuliX Script - Find and Click Favicon
# This is a Jython script that runs within SikuliX

import sys
import time

# Get the favicon image path from command line arguments
if len(sys.argv) > 1:
    favicon_image = sys.argv[1]
else:
    favicon_image = "favicon_small.png"

print("=" * 70)
print("SIKULIX VISUAL RECOGNITION")
print("=" * 70)
print("Looking for: " + favicon_image)
print("=" * 70)

try:
    # Wait a moment for the page to be ready
    wait(2)
    
    # Find the favicon on screen
    # SikuliX will search the entire screen for this image
    print("Searching for favicon on screen...")
    
    # exists() returns a Match object if found, None if not found
    match = exists(Pattern(favicon_image).similar(0.7), 10)
    
    if match:
        print("✓ Favicon found!")
        print("  Location: " + str(match))
        print("  Confidence: " + str(match.getScore()))
        
        # Highlight the match briefly so user can see what was found
        match.highlight(1)
        
        # Click on the center of the matched region
        print("Clicking on favicon...")
        click(match)
        
        print("✓ Click successful!")
        wait(2)
        
        # Exit with success
        exit(0)
    else:
        print("✗ Favicon not found on screen")
        print("  Try adjusting the similarity threshold or check if the image exists")
        exit(1)
        
except Exception as e:
    print("✗ Error: " + str(e))
    import traceback
    traceback.print_exc()
    exit(1)
