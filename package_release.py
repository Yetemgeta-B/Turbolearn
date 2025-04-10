import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

def clean_build_dirs():
    """Clean build and dist directories"""
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # Remove spec files
    for spec_file in Path('.').glob('*.spec'):
        os.remove(spec_file)
    
    print("✓ Cleaned build directories")

def create_executable():
    """Create executable using PyInstaller"""
    print("\nBuilding executable with PyInstaller...")
    
    # Determine the entry point
    main_script = "turbolearn_multiplatform.py"
    
    # Collect necessary files
    data_files = [
        ('web/static', 'web/static'),
        ('web/templates', 'web/templates')
    ]
    
    # Check if icon exists
    icon_path = "web/static/img/logo.ico"
    icon_param = f"--icon={icon_path}" if os.path.exists(icon_path) else ""
    
    # Build the PyInstaller command using python -m
    data_params = " ".join([f"--add-data '{src}{os.pathsep}{dst}'" for src, dst in data_files])
    
    # Create spec file first with all options
    cmd = (
        f"python -m pyinstaller {icon_param} "
        f"--name TurboLearnCrack "
        f"--onefile "
        f"--windowed "
        f"{data_params} "
        f"{main_script}"
    )
    
    # Fix path separator for Windows
    if platform.system() == "Windows":
        cmd = cmd.replace("'", "\"")
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("✓ Executable created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error creating executable: {e}")
        return False

def create_release_package():
    """Create a complete release package"""
    release_dir = Path("release")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # Copy executable
    exe_name = "TurboLearnCrack.exe" if platform.system() == "Windows" else "TurboLearnCrack"
    exe_path = Path("dist") / exe_name
    if exe_path.exists():
        shutil.copy(exe_path, release_dir)
    
    # Copy README and LICENSE
    for file in ["README.md", "LICENSE"]:
        if Path(file).exists():
            shutil.copy(file, release_dir)
    
    print(f"\n✓ Release package created in {release_dir.absolute()}")
    print(f"  Files to upload to GitHub Releases:")
    for file in release_dir.iterdir():
        print(f"  - {file.name}")

def main():
    print("TurboLearn Crack Release Builder")
    print("================================")
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create executable
    if create_executable():
        # Create release package
        create_release_package()
        
        print("\nGitHub Release Instructions:")
        print("1. Go to your GitHub repository")
        print("2. Click on 'Releases' in the right sidebar")
        print("3. Click 'Create a new release' or 'Draft a new release'")
        print("4. Fill in the tag version (e.g., v1.0.0)")
        print("5. Add a release title and description")
        print("6. Upload the files from the 'release' directory")
        print("7. Click 'Publish release'")
    else:
        print("\n✗ Failed to create executable, release package not created")

if __name__ == "__main__":
    main()
