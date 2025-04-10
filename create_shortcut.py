import os
import sys
import win32com.client
from pathlib import Path

def create_desktop_shortcut():
    # Get the path to the desktop
    desktop = Path(os.path.expanduser("~")) / "Desktop"
    
    # Create a shell object
    shell = win32com.client.Dispatch("WScript.Shell")
    
    # Create the shortcut
    shortcut = shell.CreateShortCut(str(desktop / "TurboLearn.lnk"))
    
    # Set the target path to the Python executable and the script
    python_exe = sys.executable
    script_path = str(Path(__file__).parent / "turbolearn_multiplatform.py")
    
    # Set shortcut properties
    shortcut.Targetpath = python_exe
    shortcut.Arguments = f'"{script_path}" --desktop'
    shortcut.WorkingDirectory = str(Path(__file__).parent)
    shortcut.IconLocation = str(Path(__file__).parent / "web" / "static" / "img" / "logo.ico")
    shortcut.Description = "TurboLearn - Advanced Learning Platform"
    
    # Save the shortcut
    shortcut.save()

if __name__ == "__main__":
    try:
        create_desktop_shortcut()
        print("Desktop shortcut created successfully!")
    except Exception as e:
        print(f"Error creating shortcut: {e}") 