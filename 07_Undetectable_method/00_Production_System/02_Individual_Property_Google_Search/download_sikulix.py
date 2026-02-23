#!/usr/bin/env python3
"""
Download SikuliX JAR file
"""
import urllib.request
import sys
import os

def download_file(url, output_path):
    """Download file with progress bar"""
    print(f"Downloading from: {url}")
    print(f"Saving to: {output_path}")
    
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            sys.stdout.write(f"\rProgress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, output_path, reporthook=report_progress)
        print("\n✓ Download complete!")
        return True
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False

if __name__ == "__main__":
    # SikuliX download URL
    url = "https://github.com/RaiMan/SikuliX1/releases/download/v2.0.5/sikulixide-2.0.5.jar"
    output = "sikulix.jar"
    
    if os.path.exists(output):
        print(f"✓ {output} already exists")
        sys.exit(0)
    
    success = download_file(url, output)
    sys.exit(0 if success else 1)
