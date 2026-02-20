#!/usr/bin/env python3
"""
Enhanced CSV Export with Auto-Path Configuration
Automatically detects and configures paths for cross-platform CSV export and download.
"""

import json
import csv
import sys
import os
from pathlib import Path
from datetime import datetime
import gc
import platform

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Define CSV columns in desired order
CSV_COLUMNS = [
    "name",
    "first_name",
    "middle_name", 
    "last_name",
    "status",
    "brokerage",
    "city",
    "sector",
    "aka",
    "drill_id",
    "email",
    "phone"
]

def get_download_folder():
    """Get the user's Downloads folder path cross-platform."""
    
    if platform.system() == "Windows":
        # Windows: Use registry to get actual Downloads folder
        try:
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, downloads_guid)[0]
                return Path(location)
        except:
            # Fallback to default
            return Path.home() / "Downloads"
    
    elif platform.system() == "Darwin":
        # macOS: Downloads folder in home directory
        return Path.home() / "Downloads"
    
    else:
        # Linux and others: Try XDG_DOWNLOAD_DIR, fallback to ~/Downloads
        try:
            # Try to read XDG user dirs config
            xdg_config = Path.home() / ".config" / "user-dirs.dirs"
            if xdg_config.exists():
                with open(xdg_config, 'r') as f:
                    for line in f:
                        if line.startswith("XDG_DOWNLOAD_DIR="):
                            # Extract path, remove quotes and $HOME
                            path = line.split('=')[1].strip().strip('"')
                            path = path.replace("$HOME", str(Path.home()))
                            return Path(path)
        except:
            pass
        
        # Fallback
        return Path.home() / "Downloads"

def get_export_path(filename="all_agents.csv", prefer_download_folder=True):
    """Get the export path, with options for project folder or Downloads folder."""
    
    if prefer_download_folder:
        # Try to save to Downloads folder for easy access
        download_path = get_download_folder()
        if download_path.exists():
            return download_path / filename
        print(f"⚠️  Downloads folder not found, using project data folder")
    
    # Default to project data folder
    return PROJECT_ROOT / "data" / filename

def export_to_csv(json_file: Path, csv_file: Path, show_path_info=True):
    """Export agent data from JSON to CSV."""
    
    # Check if JSON file exists
    if not json_file.exists():
        print(f"❌ Error: JSON file not found at {json_file}")
        return False
    
    if show_path_info:
        print("=" * 60)
        print("RECA Agent Data Export - Auto-Path Configuration")
        print("=" * 60)
        print(f"📖 Reading agents from: {json_file}")
        print(f"   File size: {json_file.stat().st_size / (1024*1024):.2f} MB")
        print(f"💾 Exporting to: {csv_file}")
        print(f"   Platform: {platform.system()}")
        
        # Show download folder info
        download_folder = get_download_folder()
        print(f"📁 Downloads folder: {download_folder}")
        if csv_file.parent == download_folder:
            print("   ✅ CSV will be saved to Downloads folder")
        else:
            print("   ⚠️  CSV will be saved to project data folder")
    
    # Load JSON data with progress indication
    try:
        if show_path_info:
            print("\n   Loading JSON data (this may take a moment for large files)...")
        with open(json_file, 'r', encoding='utf-8') as f:
            agents = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return False
    
    print(f"✅ Loaded {len(agents):,} agents")
    
    # Ensure output directory exists
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if CSV already exists
    if csv_file.exists():
        print(f"\n⚠️  CSV file already exists at {csv_file}")
        response = input("   Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("   Export cancelled.")
            return False
    
    # Write CSV with progress tracking
    print(f"\n💾 Writing CSV with progress tracking...")
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            
            # Write each agent with progress
            for i, agent in enumerate(agents, 1):
                # Ensure all required fields exist
                row = {col: agent.get(col, '') for col in CSV_COLUMNS}
                writer.writerow(row)
                
                # Progress indicator
                if i % 1000 == 0:
                    percent = (i / len(agents)) * 100
                    print(f"   Progress: {i:,}/{len(agents):,} ({percent:.1f}%)")
        
        # Clear memory
        del agents
        gc.collect()
    
    except Exception as e:
        print(f"❌ Error writing CSV: {e}")
        # Clean up partial file
        if csv_file.exists():
            csv_file.unlink()
        return False
    
    # Get file size and stats
    file_size = csv_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    print(f"\n✅ CSV export complete!")
    print(f"   📁 Location: {csv_file}")
    print(f"   📊 Records: {len(agents):,}")
    print(f"   💾 Size: {size_mb:.2f} MB")
    print(f"   ⏰ Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show file in explorer/finder
    if show_path_info:
        print(f"\n📂 To open the folder containing the CSV:")
        if platform.system() == "Windows":
            print(f"   explorer {csv_file.parent}")
        elif platform.system() == "Darwin":
            print(f"   open {csv_file.parent}")
        else:
            print(f"   xdg-open {csv_file.parent}")
    
    return True

def main():
    """Main export function with auto-path configuration."""
    
    # Parse command line arguments
    prefer_download = True
    custom_filename = None
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python export_to_csv.py [options]")
        print("Options:")
        print("  --no-download    Save to project data folder instead of Downloads")
        print("  --filename NAME  Custom filename (default: all_agents.csv)")
        print("  --help, -h       Show this help")
        return
    
    if "--no-download" in sys.argv:
        prefer_download = False
    
    if "--filename" in sys.argv:
        idx = sys.argv.index("--filename")
        if idx + 1 < len(sys.argv):
            custom_filename = sys.argv[idx + 1]
    
    # Define file paths
    json_file = PROJECT_ROOT / "data" / "all_agents.json"
    filename = custom_filename or "all_agents.csv"
    csv_file = get_export_path(filename, prefer_download)
    
    # Perform export
    success = export_to_csv(json_file, csv_file)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ EXPORT SUCCESSFUL!")
        print("\nNext steps:")
        print("1. The CSV file is ready at the location shown above")
        print("2. You can now open and analyze the data")
        print("3. Proceed to Phase 2: Email Enrichment Testing")
        print("\nTo run with different options:")
        print("  python scripts/export_to_csv.py --no-download")
        print("  python scripts/export_to_csv.py --filename my_export.csv")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ EXPORT FAILED")
        print("Please check the error messages above.")
        print("=" * 60)

if __name__ == "__main__":
    main()