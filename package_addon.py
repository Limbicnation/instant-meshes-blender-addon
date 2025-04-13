#!/usr/bin/env python3

import os
import zipfile
import shutil
from pathlib import Path

def create_addon_zip():
    """Create a zip file of the addon for distribution"""
    
    # Get the current directory
    current_dir = Path(__file__).parent.absolute()
    
    # Define the addon directory and output zip file
    addon_dir = current_dir / "instant_meshes_addon"
    zip_file = current_dir / "instant_meshes_addon.zip"
    
    # Make sure addon directory exists
    if not addon_dir.exists():
        print(f"Error: Addon directory {addon_dir} not found")
        return
    
    # Remove existing zip file if it exists
    if zip_file.exists():
        os.remove(zip_file)
    
    # Create a temporary directory for packaging
    temp_dir = current_dir / "temp_packaging"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    # Create the temporary directory and copy the addon there
    os.makedirs(temp_dir)
    shutil.copytree(addon_dir, temp_dir / "instant_meshes_addon")
    
    # Remove any __pycache__ directories or .pyc files
    for root, dirs, files in os.walk(temp_dir, topdown=True):
        for name in dirs:
            if name == "__pycache__":
                shutil.rmtree(os.path.join(root, name))
        for name in files:
            if name.endswith(".pyc"):
                os.remove(os.path.join(root, name))
    
    # Create the zip file
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate path relative to temp_dir
                rel_path = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, rel_path)
    
    # Clean up the temporary directory
    shutil.rmtree(temp_dir)
    
    print(f"Addon packaged successfully: {zip_file}")

if __name__ == "__main__":
    create_addon_zip()