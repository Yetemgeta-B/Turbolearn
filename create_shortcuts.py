import os
import sys
import platform
from pathlib import Path

def create_desktop_shortcut():
    """Create a desktop shortcut for Windows."""
    if platform.system() != 'Windows':
        print("Desktop shortcuts are only supported on Windows.")
        return False

    try:
        import win32com.client
        from win32com.shell import shell, shellcon

        # Get paths
        desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
        script_dir = Path(__file__).parent.absolute()
        python_exe = sys.executable
        script_path = script_dir / "turbolearn_multiplatform.py"

        # Create shortcut
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(os.path.join(desktop, "TurboLearn.lnk"))
        shortcut.Targetpath = python_exe
        shortcut.Arguments = f'"{script_path}"'
        shortcut.WorkingDirectory = str(script_dir)
        shortcut.IconLocation = str(script_dir / "assets" / "icon.ico")
        shortcut.save()
        print("Desktop shortcut created successfully!")
        return True
    except Exception as e:
        print(f"Error creating desktop shortcut: {e}")
        return False

def setup_mobile_shortcut():
    """Setup mobile web app for home screen installation."""
    print("\nTo add TurboLearn to your mobile home screen:")
    print("1. Open the web interface in your mobile browser")
    print("2. Look for the 'Add to Home Screen' option in your browser menu")
    print("3. Follow the prompts to install the app")
    print("\nNote: The web interface must be running to use the mobile shortcut.")
    return True

def main():
    print("TurboLearn Shortcut Creator")
    print("===========================")
    
    # Create desktop shortcut
    if platform.system() == 'Windows':
        print("\nCreating desktop shortcut...")
        if create_desktop_shortcut():
            print("✓ Desktop shortcut created successfully!")
        else:
            print("✗ Failed to create desktop shortcut.")
    
    # Setup mobile shortcut
    print("\nSetting up mobile shortcut...")
    if setup_mobile_shortcut():
        print("✓ Mobile shortcut setup instructions provided!")
    else:
        print("✗ Failed to setup mobile shortcut.")

if __name__ == "__main__":
    main() 