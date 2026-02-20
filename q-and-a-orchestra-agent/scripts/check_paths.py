#!/usr/bin/env python3
"""
Path Configuration Utility
Shows detected paths and helps users understand where files will be saved.
"""

import platform
from pathlib import Path

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

def main():
    """Show path configuration information."""
    
    print("=" * 60)
    print("RECA Project - Path Configuration Utility")
    print("=" * 60)
    
    print(f"\n🖥️  Platform: {platform.system()}")
    print(f"🏠 Home Directory: {Path.home()}")
    
    # Show Downloads folder
    downloads_path = get_download_folder()
    print(f"\n📁 Downloads Folder:")
    print(f"   Path: {downloads_path}")
    print(f"   Exists: {downloads_path.exists()}")
    
    # Show project paths
    project_root = Path(__file__).resolve().parent.parent
    data_folder = project_root / "data"
    
    print(f"\n📂 Project Paths:")
    print(f"   Project Root: {project_root}")
    print(f"   Data Folder: {data_folder}")
    print(f"   JSON File: {data_folder / 'all_agents.json'}")
    
    # Show where CSV will be saved
    csv_in_downloads = downloads_path / "all_agents.csv"
    csv_in_project = data_folder / "all_agents.csv"
    
    print(f"\n💾 CSV Export Locations:")
    print(f"   In Downloads: {csv_in_downloads}")
    print(f"   In Project: {csv_in_project}")
    
    # Check if JSON exists
    json_file = data_folder / "all_agents.json"
    if json_file.exists():
        size_mb = json_file.stat().st_size / (1024 * 1024)
        print(f"\n📊 Source JSON File:")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   Ready to export: ✅")
    else:
        print(f"\n⚠️  Source JSON file not found!")
        print(f"   Expected at: {json_file}")
    
    print("\n" + "=" * 60)
    print("Usage Examples:")
    print("=" * 60)
    print("\n# Export to Downloads folder (default):")
    print("python scripts/export_to_csv.py")
    print("\n# Export to project data folder:")
    print("python scripts/export_to_csv.py --no-download")
    print("\n# Export with custom filename:")
    print("python scripts/export_to_csv.py --filename reca_agents_2026.csv")
    print("\n# Show help:")
    print("python scripts/export_to_csv.py --help")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()