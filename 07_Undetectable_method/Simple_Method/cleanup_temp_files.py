#!/usr/bin/env python3
"""
Temporary Files Cleanup Utility
Removes screenshots, OCR data, and other temporary processing files from previous runs
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def get_directory_size(path):
    """Calculate total size of directory in bytes"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_directory_size(entry.path)
    except:
        pass
    return total


def format_size(bytes):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"


def cleanup_temp_files(dry_run=True):
    """Remove temporary processing files"""
    try:
        print("="*80)
        print("TEMPORARY FILES CLEANUP")
        print("="*80)
        if dry_run:
            print(f"\nMode: DRY RUN (no files will be deleted)")
        else:
            print(f"\nMode: LIVE (files will be deleted)")
        
        # Define what to clean up
        cleanup_targets = {
            'screenshot_sessions': {
                'pattern': 'screenshots_session_*',
                'type': 'directory',
                'description': 'Screenshot session directories'
            },
            'ocr_sessions': {
                'pattern': 'ocr_output_session_*',
                'type': 'directory',
                'description': 'OCR output session directories'
            },
            'session_json': {
                'pattern': 'property_data_session_*.json',
                'type': 'file',
                'description': 'Session JSON files'
            },
            'batch_results': {
                'pattern': '../00_Production_System/02_Individual_Property_Google_Search/batch_results',
                'type': 'directory',
                'description': 'Batch processing results (enrichment temp files)',
                'exclude': ['*.json', '*.html']  # Keep final results
            }
        }
        
        current_dir = Path('.')
        total_size = 0
        items_to_remove = []
        
        print(f"\n→ Scanning for temporary files...")
        
        # Scan for files/dirs to remove
        for target_name, target_info in cleanup_targets.items():
            pattern = target_info['pattern']
            target_type = target_info['type']
            description = target_info['description']
            
            if target_type == 'directory':
                # Find directories matching pattern
                if '*' in pattern:
                    dirs = list(current_dir.glob(pattern))
                else:
                    # Direct path
                    p = Path(pattern)
                    if p.exists() and p.is_dir():
                        dirs = [p]
                    else:
                        dirs = []
                
                for dir_path in dirs:
                    if dir_path.exists():
                        size = get_directory_size(str(dir_path))
                        total_size += size
                        items_to_remove.append({
                            'path': str(dir_path),
                            'type': 'directory',
                            'size': size,
                            'description': description
                        })
            
            elif target_type == 'file':
                # Find files matching pattern
                files = list(current_dir.glob(pattern))
                for file_path in files:
                    if file_path.exists():
                        size = file_path.stat().st_size
                        total_size += size
                        items_to_remove.append({
                            'path': str(file_path),
                            'type': 'file',
                            'size': size,
                            'description': description
                        })
        
        if not items_to_remove:
            print(f"\n✓ No temporary files found to clean up")
            return 0
        
        # Display what will be removed
        print(f"\n{'─'*80}")
        print(f"TEMPORARY FILES FOUND")
        print(f"{'─'*80}")
        
        # Group by type
        dirs_count = sum(1 for item in items_to_remove if item['type'] == 'directory')
        files_count = sum(1 for item in items_to_remove if item['type'] == 'file')
        
        print(f"\n  Directories: {dirs_count}")
        print(f"  Files: {files_count}")
        print(f"  Total size: {format_size(total_size)}\n")
        
        for item in items_to_remove:
            item_type = "📁" if item['type'] == 'directory' else "📄"
            print(f"  {item_type} {item['path']}")
            print(f"     Size: {format_size(item['size'])}")
        
        # Remove items if not dry run
        if not dry_run:
            print(f"\n{'─'*80}")
            print(f"REMOVING FILES")
            print(f"{'─'*80}\n")
            
            removed_count = 0
            removed_size = 0
            
            for item in items_to_remove:
                try:
                    if item['type'] == 'directory':
                        shutil.rmtree(item['path'])
                        print(f"  ✓ Removed directory: {item['path']}")
                    else:
                        os.remove(item['path'])
                        print(f"  ✓ Removed file: {item['path']}")
                    removed_count += 1
                    removed_size += item['size']
                except Exception as e:
                    print(f"  ✗ Failed to remove {item['path']}: {e}")
            
            print(f"\n{'─'*80}")
            print(f"CLEANUP COMPLETE")
            print(f"{'─'*80}")
            print(f"  Items removed: {removed_count}")
            print(f"  Space freed: {format_size(removed_size)}")
        
        else:
            print(f"\n{'─'*80}")
            print(f"⚠ DRY RUN mode - no files were deleted")
            print(f"  Run with --remove flag to actually delete files")
            print(f"  Potential space to free: {format_size(total_size)}")
        
        print(f"\n{'='*80}\n")
        
        return len(items_to_remove)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return -1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up temporary processing files")
    parser.add_argument('--remove', action='store_true',
                       help='Actually delete files (default is dry-run)')
    args = parser.parse_args()
    
    dry_run = not args.remove
    
    count = cleanup_temp_files(dry_run=dry_run)
    
    if count < 0:
        sys.exit(1)
    elif count == 0:
        sys.exit(0)
    else:
        sys.exit(0 if not dry_run else 2)  # Exit code 2 for dry-run with files found
