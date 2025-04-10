import os
import sys
import platform
import subprocess
import webbrowser
import threading
import time
from pathlib import Path

# Determine if we're running in a packaged environment (PyInstaller)
def is_packaged():
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# Get the application directory
def get_app_dir():
    if is_packaged():
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent

# Detect platform and architecture
def get_platform_info():
    system = platform.system().lower()
    architecture = platform.machine().lower()
    
    # Map common architectures to more user-friendly names
    arch_map = {
        'x86_64': 'x64',
        'amd64': 'x64',
        'i386': 'x86',
        'i686': 'x86',
        'armv7l': 'arm',
        'armv8': 'arm64',
        'aarch64': 'arm64'
    }
    
    if architecture in arch_map:
        architecture = arch_map[architecture]
    
    return system, architecture

# Check if running on mobile
def is_mobile():
    # On typical deployments, this won't detect mobile directly
    # This is more for when the app is deployed as a PWA or web app
    system, arch = get_platform_info()
    
    # Detect Android using environment variable that might be set if using something like Termux
    if 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ:
        return True
    
    # For iOS, there's no reliable way to detect from Python directly
    # Generally, mobile users will access via the web interface
    
    return False

# Start web server for API access
def start_web_server():
    try:
        # Import the web API module
        from turbolearn_api import app
        
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 5000))
        
        # Start the Flask app
        app.run(host='0.0.0.0', port=port, debug=False)
    except ImportError:
        print("Error: Could not import the web API module. Please ensure it is installed.")
        sys.exit(1)

# Start desktop GUI
def start_desktop_gui():
    try:
        # Import the desktop GUI module
        import customtkinter as ctk
        from turbolearn_gui import TurboLearnGUI
        
        # Initialize and start the GUI
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        app = TurboLearnGUI()
        app.mainloop()
    except ImportError:
        print("Error: Could not import the desktop GUI module. Please ensure it is installed.")
        sys.exit(1)

# Open web interface in browser
def open_web_interface(port=5000):
    # Give the server time to start
    time.sleep(2)
    
    # Open browser to the web interface
    webbrowser.open(f"http://localhost:{port}")

# Check requirements and install if necessary
def check_requirements():
    try:
        # Check if pip is available
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        
        # Get the requirements file path
        requirements_path = get_app_dir() / "requirements.txt"
        
        if requirements_path.exists():
            print("Checking and installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
                         stdout=subprocess.PIPE, 
                         check=True)
    except subprocess.CalledProcessError:
        print("Warning: Could not verify or install dependencies.")
    except FileNotFoundError:
        print("Warning: Requirements file not found.")

def main():
    print("TurboLearn Multi-Platform Launcher")
    print("==================================")
    
    # Check if arguments were provided
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == '--web' or arg == '-w':
            # Force web interface
            print("Starting web interface as requested...")
            thread = threading.Thread(target=start_web_server)
            thread.daemon = True
            thread.start()
            open_web_interface()
            # Keep the main thread alive
            try:
                while thread.is_alive():
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
            return
            
        elif arg == '--desktop' or arg == '-d':
            # Force desktop interface
            print("Starting desktop interface as requested...")
            start_desktop_gui()
            return
            
        elif arg == '--help' or arg == '-h':
            print("Usage: python turbolearn_multiplatform.py [OPTION]")
            print("Options:")
            print("  --web, -w       Start the web interface")
            print("  --desktop, -d   Start the desktop interface")
            print("  --help, -h      Show this help message")
            return
    
    # Check and install requirements
    check_requirements()
    
    # Detect platform
    system, architecture = get_platform_info()
    print(f"Detected platform: {system} ({architecture})")
    
    # Handle different platforms
    if is_mobile():
        print("Mobile platform detected, starting web interface...")
        start_web_server()
    elif system == 'windows' or system == 'darwin' or system == 'linux':
        # On desktop platforms, start both the GUI and the API server
        # This allows for remote access while still providing native interface
        print("Desktop platform detected, starting hybrid mode...")
        
        # Start the web server in a separate thread
        thread = threading.Thread(target=start_web_server)
        thread.daemon = True
        thread.start()
        
        # Optionally open the web interface
        # web_interface_thread = threading.Thread(target=open_web_interface)
        # web_interface_thread.daemon = True
        # web_interface_thread.start()
        
        # Start the desktop GUI in the main thread
        start_desktop_gui()
    else:
        # For unknown platforms, default to web interface
        print("Platform not recognized, defaulting to web interface...")
        start_web_server()

if __name__ == "__main__":
    main() 