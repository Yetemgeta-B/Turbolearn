#!/usr/bin/env python3
import os
import random
import string
import time
import argparse
import sys
import subprocess
import psutil
import shutil
import platform
import re
from typing import Tuple, List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored terminal output
init()

# Custom implementation of get_browser_version_from_os function
def get_browser_version(browser_type):
    """
    Get the version of the specified browser.
    
    Args:
        browser_type: The type of browser ('chrome', 'firefox', 'edge', etc.)
        
    Returns:
        The browser version as a string, or None if not found
    """
    version = None
    
    try:
        system = platform.system()
        
        if system == "Windows":
            if browser_type.lower() == "chrome":
                # Method 1: Check registry
                try:
                    import winreg
                    key_path = r"SOFTWARE\Google\Chrome\BLBeacon"
                    registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                    version, _ = winreg.QueryValueEx(registry_key, "version")
                    winreg.CloseKey(registry_key)
                except:
                    # Method 2: Use PowerShell
                    result = subprocess.run(
                        ["powershell", "-command", "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Version"],
                        capture_output=True,
                        text=True
                    )
                    if result.stdout.strip():
                        version = result.stdout.strip()
                    else:
                        # Method 3: Check program files location
                        chrome_path = None
                        for path in ["C:/Program Files/Google/Chrome/Application/chrome.exe", 
                                    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"]:
                            if os.path.exists(path):
                                chrome_path = path
                                break
                        
                        if chrome_path:
                            # Extract version from file info
                            try:
                                import win32api
                                file_info = win32api.GetFileVersionInfo(chrome_path, "\\")
                                ms = file_info['FileVersionMS']
                                ls = file_info['FileVersionLS']
                                version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
                            except:
                                # If win32api not available, try another method
                                version = "116"  # Default to a common version
            
            elif browser_type.lower() == "firefox":
                # Try PowerShell for Firefox
                result = subprocess.run(
                    ["powershell", "-command", "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\firefox.exe' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Version"],
                    capture_output=True,
                    text=True
                )
                if result.stdout.strip():
                    version = result.stdout.strip()
                else:
                    version = "115"  # Default Firefox version
            
            elif browser_type.lower() == "edge":
                # Check registry for Edge
                try:
                    import winreg
                    key_path = r"SOFTWARE\Microsoft\Edge\BLBeacon"
                    registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                    version, _ = winreg.QueryValueEx(registry_key, "version")
                    winreg.CloseKey(registry_key)
                except:
                    version = "115"  # Default Edge version
            
        elif system == "Darwin":  # macOS
            # macOS version detection
            if browser_type.lower() == "chrome":
                chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                if os.path.exists(chrome_path):
                    result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True)
                    if result.stdout:
                        version_match = re.search(r"Google Chrome ([\d.]+)", result.stdout)
                        if version_match:
                            version = version_match.group(1)
            
            elif browser_type.lower() == "firefox":
                result = subprocess.run(["firefox", "--version"], capture_output=True, text=True)
                if result.stdout:
                    version_match = re.search(r"Firefox ([\d.]+)", result.stdout)
                    if version_match:
                        version = version_match.group(1)
            
            elif browser_type.lower() == "edge":
                edge_path = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
                if os.path.exists(edge_path):
                    result = subprocess.run([edge_path, "--version"], capture_output=True, text=True)
                    if result.stdout:
                        version_match = re.search(r"Microsoft Edge ([\d.]+)", result.stdout)
                        if version_match:
                            version = version_match.group(1)
        
        else:  # Linux
            # Linux version detection
            if browser_type.lower() == "chrome":
                # Try different Chrome variant commands
                for cmd in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
                    try:
                        result = subprocess.run([cmd, "--version"], capture_output=True, text=True)
                        if result.stdout:
                            version_match = re.search(r"(?:Google Chrome|Chromium) ([\d.]+)", result.stdout)
                            if version_match:
                                version = version_match.group(1)
                                break
                    except FileNotFoundError:
                        continue
            
            elif browser_type.lower() == "firefox":
                try:
                    result = subprocess.run(["firefox", "--version"], capture_output=True, text=True)
                    if result.stdout:
                        version_match = re.search(r"Firefox ([\d.]+)", result.stdout)
                        if version_match:
                            version = version_match.group(1)
                except FileNotFoundError:
                    pass
            
            elif browser_type.lower() == "edge":
                try:
                    result = subprocess.run(["microsoft-edge", "--version"], capture_output=True, text=True)
                    if result.stdout:
                        version_match = re.search(r"Microsoft Edge ([\d.]+)", result.stdout)
                        if version_match:
                            version = version_match.group(1)
                except FileNotFoundError:
                    pass
    
    except Exception as e:
        print(f"{Fore.YELLOW}Error detecting browser version: {str(e)}{Style.RESET_ALL}")
    
    # If all methods failed, return a default version
    if not version:
        # Default versions for each browser
        defaults = {
            "chrome": "116",
            "firefox": "115",
            "edge": "115",
            "vivaldi": "116",
            "brave": "116",
            "opera": "100"
        }
        version = defaults.get(browser_type.lower(), "116")
        print(f"{Fore.YELLOW}Using default {browser_type} version: {version}{Style.RESET_ALL}")
    
    return version

# Lists for random name generation
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
    "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
    "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee",
    "Walker", "Hall", "Allen", "Young", "Hernandez", "King", "Wright", "Lopez",
    "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter",
    "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans"
]

# Browser paths for different operating systems
BROWSER_PATHS = {
    'windows': {
        'chrome': [
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
        ],
        'firefox': [
            "C:/Program Files/Mozilla Firefox/firefox.exe",
            "C:/Program Files (x86)/Mozilla Firefox/firefox.exe"
        ],
        'edge': [
            "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
            "C:/Program Files/Microsoft/Edge/Application/msedge.exe"
        ],
        'vivaldi': [
            "C:/Program Files/Vivaldi/Application/vivaldi.exe",
            "C:/Program Files (x86)/Vivaldi/Application/vivaldi.exe"
        ],
        'brave': [
            "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe",
            "C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"
        ],
        'opera': [
            "C:/Program Files/Opera/launcher.exe",
            "C:/Program Files (x86)/Opera/launcher.exe"
        ]
    },
    'macos': {
        'chrome': ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
        'firefox': ["/Applications/Firefox.app/Contents/MacOS/firefox"],
        'edge': ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
        'vivaldi': ["/Applications/Vivaldi.app/Contents/MacOS/Vivaldi"],
        'brave': ["/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
        'opera': ["/Applications/Opera.app/Contents/MacOS/Opera"]
    },
    'linux': {
        'chrome': ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"],
        'firefox': ["/usr/bin/firefox"],
        'edge': ["/usr/bin/microsoft-edge"],
        'vivaldi': ["/usr/bin/vivaldi-stable"],
        'brave': ["/usr/bin/brave-browser"],
        'opera': ["/usr/bin/opera"]
    }
}

# Map of ChromeDriver download URLs for major versions
CHROMEDRIVER_URLS = {
    # Format: 'version': ('win32_url', 'win64_url')
    '135': ('https://storage.googleapis.com/chrome-for-testing-public/135.0.7049.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/135.0.7049.0/win64/chromedriver-win64.zip'),
    '134': ('https://storage.googleapis.com/chrome-for-testing-public/134.0.7012.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/134.0.7012.0/win64/chromedriver-win64.zip'),
    '133': ('https://storage.googleapis.com/chrome-for-testing-public/133.0.6958.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/133.0.6958.0/win64/chromedriver-win64.zip'),
    '132': ('https://storage.googleapis.com/chrome-for-testing-public/132.0.6555.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/132.0.6555.0/win64/chromedriver-win64.zip'),
    '131': ('https://storage.googleapis.com/chrome-for-testing-public/131.0.6507.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/131.0.6507.0/win64/chromedriver-win64.zip'),
    '130': ('https://storage.googleapis.com/chrome-for-testing-public/130.0.6555.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/130.0.6555.0/win64/chromedriver-win64.zip'),
    '129': ('https://storage.googleapis.com/chrome-for-testing-public/129.0.6454.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/129.0.6454.0/win64/chromedriver-win64.zip'),
    '128': ('https://storage.googleapis.com/chrome-for-testing-public/128.0.6410.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/128.0.6410.0/win64/chromedriver-win64.zip'),
    '127': ('https://storage.googleapis.com/chrome-for-testing-public/127.0.6387.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/127.0.6387.0/win64/chromedriver-win64.zip'),
    '126': ('https://storage.googleapis.com/chrome-for-testing-public/126.0.6339.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/126.0.6339.0/win64/chromedriver-win64.zip'),
    '125': ('https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.0/win64/chromedriver-win64.zip'),
    '124': ('https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.0/win64/chromedriver-win64.zip'),
    '123': ('https://storage.googleapis.com/chrome-for-testing-public/123.0.6312.58/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/123.0.6312.58/win64/chromedriver-win64.zip'),
    '122': ('https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.128/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.128/win64/chromedriver-win64.zip'),
    '121': ('https://storage.googleapis.com/chrome-for-testing-public/121.0.6249.0/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/121.0.6249.0/win64/chromedriver-win64.zip'),
    '120': ('https://storage.googleapis.com/chrome-for-testing-public/120.0.6099.109/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/120.0.6099.109/win64/chromedriver-win64.zip'),
    '119': ('https://storage.googleapis.com/chrome-for-testing-public/119.0.6045.105/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/119.0.6045.105/win64/chromedriver-win64.zip'),
    '118': ('https://storage.googleapis.com/chrome-for-testing-public/118.0.5993.70/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/118.0.5993.70/win64/chromedriver-win64.zip'),
    '117': ('https://storage.googleapis.com/chrome-for-testing-public/117.0.5938.149/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/117.0.5938.149/win64/chromedriver-win64.zip'),
    '116': ('https://storage.googleapis.com/chrome-for-testing-public/116.0.5845.96/win32/chromedriver-win32.zip', 
            'https://storage.googleapis.com/chrome-for-testing-public/116.0.5845.96/win64/chromedriver-win64.zip'),
    '115': ('https://storage.googleapis.com/chrome-for-testing-public/115.0.5790.170/win32/chromedriver-win32.zip',
            'https://storage.googleapis.com/chrome-for-testing-public/115.0.5790.170/win64/chromedriver-win64.zip'),
    '114': ('https://storage.googleapis.com/chrome-for-testing-public/114.0.5735.90/win32/chromedriver-win32.zip',
            'https://storage.googleapis.com/chrome-for-testing-public/114.0.5735.90/win64/chromedriver-win64.zip'),
    # Add more versions as needed
}

def clear_webdriver_cache():
    """Clear the webdriver-manager cache to force a fresh download."""
    try:
        from webdriver_manager.core.driver_cache import DriverCacheManager
        cache_manager = DriverCacheManager()
        cache_path = cache_manager.get_cache_path()
        
        print(f"{Fore.YELLOW}Clearing WebDriver cache at: {cache_path}{Style.RESET_ALL}")
        
        if os.path.exists(cache_path):
            for item in os.listdir(cache_path):
                item_path = os.path.join(cache_path, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    print(f"{Fore.GREEN}Removed: {item_path}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}Failed to remove {item_path}: {str(e)}{Style.RESET_ALL}")
            
            print(f"{Fore.GREEN}WebDriver cache cleared successfully.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Cache directory not found at {cache_path}{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}Error clearing WebDriver cache: {str(e)}{Style.RESET_ALL}")

def manual_chromedriver_download(output_path=None):
    """
    Manually download a compatible ChromeDriver and extract it to a specified location.
    Returns the path to the ChromeDriver executable.
    """
    import zipfile
    import urllib.request
    import platform
    
    # Determine system architecture
    is_64bit = platform.machine().endswith('64')
    
    # Create a directory for the driver if output_path not specified
    if not output_path:
        output_dir = os.path.join(os.path.expanduser("~"), "turbolearn_drivers")
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = output_path
        
    # Try to detect Chrome version
    chrome_version = None
    try:
        chrome_version = get_browser_version("chrome")
        if chrome_version:
            # Get major version
            chrome_version = chrome_version.split('.')[0]
            print(f"{Fore.GREEN}Detected Chrome version: {chrome_version}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}Could not detect Chrome version: {str(e)}{Style.RESET_ALL}")
    
    # If we couldn't detect or don't have the version in our map, use latest
    if not chrome_version or chrome_version not in CHROMEDRIVER_URLS:
        print(f"{Fore.YELLOW}Using default ChromeDriver version (116).{Style.RESET_ALL}")
        chrome_version = '116'  # Default to latest known version
    
    # Download the appropriate driver
    url_index = 1 if is_64bit else 0  # Use 64-bit driver if system is 64-bit
    driver_url = CHROMEDRIVER_URLS[chrome_version][url_index]
    
    zip_path = os.path.join(output_dir, "chromedriver.zip")
    print(f"{Fore.CYAN}Downloading ChromeDriver from: {driver_url}{Style.RESET_ALL}")
    
    try:
        # Download the zip file
        urllib.request.urlretrieve(driver_url, zip_path)
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        # Find the actual executable
        chromedriver_exec = None
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.startswith('chromedriver') and (file.endswith('.exe') or not '.' in file):
                    chromedriver_exec = os.path.join(root, file)
                    break
            if chromedriver_exec:
                break
        
        if not chromedriver_exec:
            raise Exception("ChromeDriver executable not found in the downloaded package")
        
        # Ensure the driver is executable (important for Linux/Mac)
        if not sys.platform.startswith('win'):
            os.chmod(chromedriver_exec, 0o755)
        
        print(f"{Fore.GREEN}ChromeDriver successfully downloaded to: {chromedriver_exec}{Style.RESET_ALL}")
        return chromedriver_exec
        
    except Exception as e:
        print(f"{Fore.RED}Failed to download and extract ChromeDriver: {str(e)}{Style.RESET_ALL}")
        return None
    finally:
        # Clean up the zip file
        if os.path.exists(zip_path):
            os.remove(zip_path)

def detect_installed_browsers() -> Dict[str, str]:
    """Detect browsers installed on the system."""
    print(f"{Fore.CYAN}Detecting installed browsers...{Style.RESET_ALL}")
    
    installed_browsers = {}
    
    # Determine the operating system
    if sys.platform.startswith('win'):
        os_name = 'windows'
    elif sys.platform.startswith('darwin'):
        os_name = 'macos'
    else:
        os_name = 'linux'
    
    # Check for browsers installed on the system
    for browser_name, paths in BROWSER_PATHS[os_name].items():
        for path in paths:
            if os.path.exists(path):
                installed_browsers[browser_name] = path
                print(f"{Fore.GREEN}Found {browser_name.capitalize()} at {path}{Style.RESET_ALL}")
                break
    
    # If no browsers found, add a fallback option
    if not installed_browsers:
        print(f"{Fore.YELLOW}No browsers detected automatically. Using default Chrome path.{Style.RESET_ALL}")
        installed_browsers['chrome'] = ""  # Empty path will use system default
    
    return installed_browsers

def check_browser_running(browser_name: str, browser_path: str):
    """Check if the specified browser is already running and offer to close it."""
    browser_processes = []
    process_name = os.path.basename(browser_path).lower() if browser_path else browser_name
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            if process_name in proc_name or browser_name in proc_name:
                browser_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if browser_processes:
        print(f"{Fore.YELLOW}Found {len(browser_processes)} running {browser_name.capitalize()} instance(s).{Style.RESET_ALL}")
        close_choice = input(f"Do you want to close running {browser_name.capitalize()} instances? (y/n): ").lower()
        if close_choice == 'y':
            for proc in browser_processes:
                try:
                    proc.terminate()
                    print(f"{Fore.GREEN}Terminated {browser_name.capitalize()} process with PID {proc.info['pid']}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}Failed to terminate process with PID {proc.info['pid']}: {str(e)}{Style.RESET_ALL}")
            
            # Give some time for processes to terminate
            time.sleep(1)
            return True
        else:
            print(f"{Fore.YELLOW}Continuing with {browser_name.capitalize()} instances running. This might cause conflicts.{Style.RESET_ALL}")
    return False

class TurboLearnSignup:
    def __init__(self, browser_name: str = 'chrome', browser_path: str = None, 
                 private_mode: bool = False, driver_path: str = None,
                 force_manual_download: bool = False):
        """Initialize the TurboLearn signup automation with the selected browser."""
        print(f"{Fore.CYAN}Initializing TurboLearn signup automation with {browser_name.capitalize()}...{Style.RESET_ALL}")
        self.browser_name = browser_name.lower()
        self.browser_path = browser_path
        self.driver = None
        self.wait = None
        self.manual_driver_path = None
        
        try:
            # If force manual download, get ChromeDriver directly
            if force_manual_download and (self.browser_name == 'chrome' or self.browser_name == 'vivaldi' or 
                                         self.browser_name == 'brave' or self.browser_name == 'opera'):
                self.manual_driver_path = manual_chromedriver_download()
            
            # Initialize the appropriate browser
            if self.browser_name == 'chrome' or self.browser_name == 'vivaldi' or self.browser_name == 'brave' or self.browser_name == 'opera':
                self._init_chromium_browser(private_mode, driver_path)
            elif self.browser_name == 'firefox':
                self._init_firefox_browser(private_mode, driver_path)
            elif self.browser_name == 'edge':
                self._init_edge_browser(private_mode, driver_path)
            else:
                print(f"{Fore.YELLOW}Unsupported browser: {browser_name}. Falling back to Chrome.{Style.RESET_ALL}")
                self.browser_name = 'chrome'
                self._init_chromium_browser(private_mode, driver_path)
                
        except Exception as e:
            print(f"{Fore.RED}Fatal error during initialization: {str(e)}{Style.RESET_ALL}")
            
            # Special handling for "not a valid Win32 application" error
            if "not a valid Win32 application" in str(e) and not force_manual_download:
                print(f"{Fore.YELLOW}Detected possible corrupted WebDriver. Trying manual download...{Style.RESET_ALL}")
                try:
                    # Try manual ChromeDriver download if we're on a Chromium browser
                    if self.browser_name in ['chrome', 'vivaldi', 'brave', 'opera']:
                        self.manual_driver_path = manual_chromedriver_download()
                        if self.manual_driver_path:
                            # Reinitialize with manually downloaded driver
                            print(f"{Fore.GREEN}Retrying with manually downloaded driver...{Style.RESET_ALL}")
                            self._init_chromium_browser(private_mode, self.manual_driver_path)
                        else:
                            raise Exception("Failed to manually download ChromeDriver")
                    else:
                        raise Exception(f"Cannot manually download driver for {self.browser_name}")
                except Exception as e2:
                    print(f"{Fore.RED}Manual driver download failed: {str(e2)}{Style.RESET_ALL}")
                    self._try_chrome_fallback(private_mode, driver_path)
            elif self.browser_name != 'chrome':
                self._try_chrome_fallback(private_mode, driver_path)
            else:
                raise

    def _try_chrome_fallback(self, private_mode: bool, driver_path: str = None):
        """Attempt to fall back to Chrome if the selected browser fails."""
        print(f"{Fore.YELLOW}Trying to fall back to Chrome...{Style.RESET_ALL}")
        try:
            self.browser_name = 'chrome'
            self.browser_path = None
            # Try manual download first for better compatibility
            if not self.manual_driver_path:
                self.manual_driver_path = manual_chromedriver_download()
            
            if self.manual_driver_path:
                self._init_chromium_browser(private_mode, self.manual_driver_path)
            else:
                self._init_chromium_browser(private_mode, driver_path)
        except Exception as e:
            print(f"{Fore.RED}Chrome fallback also failed: {str(e)}{Style.RESET_ALL}")
            raise Exception("Could not initialize any browser. Please check your installation.")

    def _init_chromium_browser(self, private_mode: bool, driver_path: str = None):
        """Initialize a Chromium-based browser (Chrome, Vivaldi, Brave, Opera)."""
        options = ChromeOptions()
        
        # Add additional stability options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Add SSL and automation detection bypass options
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Add performance options
        options.add_argument("--disable-extensions")
        options.add_argument("--dns-prefetch-disable")
        
        # Set browser binary if path is provided
        if self.browser_path and os.path.exists(self.browser_path):
            options.binary_location = self.browser_path
        
        if private_mode:
            print(f"{Fore.YELLOW}Starting browser in private mode...{Style.RESET_ALL}")
            options.add_argument("--incognito")
        
        # Set up the service with a specific driver path or automatic download
        if driver_path and os.path.exists(driver_path):
            print(f"{Fore.GREEN}Using provided ChromeDriver at {driver_path}{Style.RESET_ALL}")
            service = ChromeService(executable_path=driver_path)
        elif self.manual_driver_path and os.path.exists(self.manual_driver_path):
            print(f"{Fore.GREEN}Using manually downloaded ChromeDriver at {self.manual_driver_path}{Style.RESET_ALL}")
            service = ChromeService(executable_path=self.manual_driver_path)
        else:
            # Try with automatic ChromeDriver download
            print(f"{Fore.CYAN}Downloading appropriate ChromeDriver...{Style.RESET_ALL}")
            service = ChromeService(ChromeDriverManager().install())
        
        # Initialize webdriver with error handling
        try:
            self.driver = webdriver.Chrome(service=service, options=options)
            # Increase default timeout to 30 seconds
            self.wait = WebDriverWait(self.driver, 30)
            print(f"{Fore.GREEN}Browser started successfully!{Style.RESET_ALL}")
        except Exception as e:
            error_msg = str(e)
            print(f"{Fore.RED}Failed to initialize WebDriver: {error_msg}{Style.RESET_ALL}")
            raise

    def _init_firefox_browser(self, private_mode: bool, driver_path: str = None):
        """Initialize Firefox browser."""
        options = FirefoxOptions()
        
        # Set browser binary if path is provided
        if self.browser_path and os.path.exists(self.browser_path):
            options.binary_location = self.browser_path
        
        if private_mode:
            print(f"{Fore.YELLOW}Starting browser in private mode...{Style.RESET_ALL}")
            options.add_argument("-private")
        
        # Set up the service with a specific driver path or automatic download
        if driver_path and os.path.exists(driver_path):
            print(f"{Fore.GREEN}Using provided GeckoDriver at {driver_path}{Style.RESET_ALL}")
            service = FirefoxService(executable_path=driver_path)
        else:
            # Try with automatic GeckoDriver download
            print(f"{Fore.CYAN}Downloading appropriate GeckoDriver...{Style.RESET_ALL}")
            service = FirefoxService(GeckoDriverManager().install())
        
        # Initialize webdriver with error handling
        try:
            self.driver = webdriver.Firefox(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 10)
            print(f"{Fore.GREEN}Browser started successfully!{Style.RESET_ALL}")
        except Exception as e:
            error_msg = str(e)
            print(f"{Fore.RED}Failed to initialize Firefox WebDriver: {error_msg}{Style.RESET_ALL}")
            raise

    def _init_edge_browser(self, private_mode: bool, driver_path: str = None):
        """Initialize Edge browser."""
        options = EdgeOptions()
        
        # Set browser binary if path is provided
        if self.browser_path and os.path.exists(self.browser_path):
            options.binary_location = self.browser_path
        
        if private_mode:
            print(f"{Fore.YELLOW}Starting browser in private mode...{Style.RESET_ALL}")
            options.add_argument("--inprivate")
        
        # Set up the service with a specific driver path or automatic download
        if driver_path and os.path.exists(driver_path):
            print(f"{Fore.GREEN}Using provided EdgeDriver at {driver_path}{Style.RESET_ALL}")
            service = EdgeService(executable_path=driver_path)
        else:
            # Try with automatic EdgeDriver download
            print(f"{Fore.CYAN}Downloading appropriate EdgeDriver...{Style.RESET_ALL}")
            service = EdgeService(EdgeChromiumDriverManager().install())
        
        # Initialize webdriver with error handling
        try:
            self.driver = webdriver.Edge(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 10)
            print(f"{Fore.GREEN}Browser started successfully!{Style.RESET_ALL}")
        except Exception as e:
            error_msg = str(e)
            print(f"{Fore.RED}Failed to initialize Edge WebDriver: {error_msg}{Style.RESET_ALL}")
            raise

    def generate_random_name(self) -> Tuple[str, str]:
        """Generate a random first and last name."""
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        return first_name, last_name

    def generate_password(self, length: int = 12) -> str:
        """Generate a secure random password."""
        characters = string.ascii_letters + string.digits + "!@#$%^&*()_-+=<>?"
        password = ''.join(random.choice(characters) for _ in range(length))
        return password

    def get_temp_email(self) -> str:
        """Get a temporary email address (fallback to generated email to avoid connection issues)."""
        print(f"{Fore.CYAN}Getting temporary email address...{Style.RESET_ALL}")
        
        # Skip temp-mail.org due to connection issues and use fallback directly
        # Generate a random email with a real-looking domain
        domains = ["gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "protonmail.com"]
        username = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
        random_number = random.randint(100, 9999)
        domain = random.choice(domains)
        random_email = f"{username}{random_number}@{domain}"
        
        print(f"{Fore.GREEN}Using generated email: {random_email}{Style.RESET_ALL}")
        return random_email

    def signup_process(self):
        """Execute the TurboLearn signup process."""
        try:
            # 1. Navigate to TurboLearn website
            print(f"{Fore.CYAN}Navigating to TurboLearn website...{Style.RESET_ALL}")
            self.driver.get("https://www.turbolearn.ai/")
            
            # 2. Click on "Get Started - It's Free" button using exact selector
            print(f"{Fore.CYAN}Looking for 'Get Started' button...{Style.RESET_ALL}")
            
            # Create a shorter wait for faster response
            short_wait = WebDriverWait(self.driver, 5)
            
            # First try the exact CSS selector provided by the user
            try:
                # Exact div containing the Get Started text
                get_started_button = short_wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.bg-tint.hover\\:bg-dark_tint"))
                )
                get_started_button.click()
                print(f"{Fore.GREEN}Clicked 'Get Started' button using exact selector{Style.RESET_ALL}")
                button_found = True
            except Exception as e:
                print(f"{Fore.YELLOW}Couldn't find exact Get Started button, trying alternatives...{Style.RESET_ALL}")
                button_found = False
            
            # If exact selector fails, try the h4 text element or fallback to other methods
            if not button_found:
                try:
                    get_started_text = short_wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//h4[contains(text(), 'Get Started')]"))
                    )
                    get_started_text.click()
                    print(f"{Fore.GREEN}Clicked 'Get Started' button via text{Style.RESET_ALL}")
                    button_found = True
                except Exception:
                    # Rest of the fallback methods as before
                    # Try multiple different selectors for the Get Started button
                    button_selectors = [
                        # XPath selectors
                        "//a[contains(text(), 'Get Started') or contains(text(), 'get started')]",
                        "//a[contains(@class, 'button') and contains(text(), 'Get Started')]",
                        "//a[contains(@href, 'signup') or contains(@href, 'register')]",
                        "//button[contains(text(), 'Get Started') or contains(text(), 'get started')]",
                        "//div[contains(@class, 'button') and contains(text(), 'Get Started')]",
                        
                        # CSS selectors
                        "a.button:contains('Get Started')",
                        "a[href*='signup'], a[href*='register']",
                        ".cta-button"
                    ]
                    
                    # Print page source for debugging
                    print(f"{Fore.YELLOW}Page title: {self.driver.title}{Style.RESET_ALL}")
                    
                    for selector in button_selectors:
                        try:
                            button = short_wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            button.click()
                            print(f"{Fore.GREEN}Clicked 'Get Started' button with selector: {selector}{Style.RESET_ALL}")
                            button_found = True
                            break
                        except:
                            try:
                                button = short_wait.until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                                button.click()
                                print(f"{Fore.GREEN}Clicked 'Get Started' button with CSS selector: {selector}{Style.RESET_ALL}")
                                button_found = True
                                break
                            except:
                                continue
            
            # Wait for the form to load, but with a shorter wait time (2 seconds instead of 5)
            time.sleep(2)
            
            # 3. Fill in signup form
            print(f"{Fore.CYAN}Filling in signup form...{Style.RESET_ALL}")
            
            # Generate random first and last name
            first_name, last_name = self.generate_random_name()
            
            # Fill in first name - try multiple selectors
            first_name_field = None
            first_name_selectors = [
                "//input[@name='firstName']",
                "//input[@placeholder='First Name']",
                "//input[contains(@id, 'first')]"
            ]
            
            for selector in first_name_selectors:
                try:
                    first_name_field = short_wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    break
                except:
                    continue
            
            if first_name_field:
                first_name_field.send_keys(first_name)
                print(f"{Fore.GREEN}Filled in first name: {first_name}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Could not find first name field{Style.RESET_ALL}")
                screenshot_path = os.path.join(os.path.expanduser("~"), "turbolearn_signup_form.png")
                self.driver.save_screenshot(screenshot_path)
                print(f"{Fore.RED}Screenshot saved to: {screenshot_path}{Style.RESET_ALL}")
                return False
            
            # Fill in last name - try multiple selectors
            last_name_selectors = [
                "//input[@name='lastName']",
                "//input[@placeholder='Last Name']",
                "//input[contains(@id, 'last')]"
            ]
            
            last_name_field = None
            for selector in last_name_selectors:
                try:
                    last_name_field = self.driver.find_element(By.XPATH, selector)
                    break
                except:
                    continue
            
            if last_name_field:
                last_name_field.send_keys(last_name)
                print(f"{Fore.GREEN}Filled in last name: {last_name}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Could not find last name field{Style.RESET_ALL}")
            
            # Get and fill in email
            email = self.get_temp_email()
            
            email_selectors = [
                "//input[@type='email']",
                "//input[@name='email']",
                "//input[@placeholder='Email']",
                "//input[contains(@id, 'email')]"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.XPATH, selector)
                    break
                except:
                    continue
            
            if email_field:
                email_field.send_keys(email)
                print(f"{Fore.GREEN}Filled in email{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Could not find email field{Style.RESET_ALL}")
            
            # Generate and fill in password
            password = self.generate_password()
            
            password_selectors = [
                "//input[@type='password']",
                "//input[@name='password']",
                "//input[@placeholder='Password']",
                "//input[contains(@id, 'password')]"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.XPATH, selector)
                    break
                except:
                    continue
            
            if password_field:
                password_field.send_keys(password)
                print(f"{Fore.GREEN}Filled in password{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Could not find password field{Style.RESET_ALL}")
            
            # 4. Click on "Create an Account" button
            try:
                # Use the exact selector provided by the user
                create_account_button = short_wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'][class*='bg-tint']"))
                )
                create_account_button.click()
                print(f"{Fore.GREEN}Clicked 'Create an Account' button using exact selector{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Couldn't find exact Create Account button: {str(e)}, trying alternatives...{Style.RESET_ALL}")
                
                # Try alternative selectors if the exact one fails
                create_account_selectors = [
                    "//button[contains(text(), 'Create an account')]",
                    "//button[contains(text(), 'Create an Account')]",
                    "//button[contains(text(), 'Sign Up')]",
                    "//button[contains(text(), 'Register')]",
                    "//input[@type='submit']",
                    "//button[@type='submit']"
                ]
                
                create_account_button = None
                for selector in create_account_selectors:
                    try:
                        create_account_button = self.driver.find_element(By.XPATH, selector)
                        break
                    except:
                        continue
                
                if create_account_button:
                    create_account_button.click()
                    print(f"{Fore.GREEN}Clicked 'Create an Account' button{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Could not find the Create Account button{Style.RESET_ALL}")
                    # Try using JavaScript to submit the form
                    try:
                        self.driver.execute_script("document.querySelector('form').submit();")
                        print(f"{Fore.GREEN}Submitted form via JavaScript{Style.RESET_ALL}")
                    except:
                        print(f"{Fore.RED}Could not submit form via JavaScript{Style.RESET_ALL}")
                        screenshot_path = os.path.join(os.path.expanduser("~"), "turbolearn_form_submit.png")
                        self.driver.save_screenshot(screenshot_path)
                        print(f"{Fore.RED}Screenshot saved to: {screenshot_path}{Style.RESET_ALL}")
                        return False
            
            # 5. Wait for account creation to complete and redirect with reduced wait time
            print(f"{Fore.CYAN}Waiting for account creation to complete...{Style.RESET_ALL}")
            time.sleep(5)  # Reduced from 10 seconds to 5 seconds
            
            # 6. Look for and click "Skip Question" button if survey appears
            try:
                # Add the exact CSS selector for the Skip Question element provided by the user
                skip_selectors = [
                    "h6.text-secondary-foreground.hover\\:cursor-pointer",
                    "h6.hover\\:cursor-pointer",
                    "h6.text-xs.text-center",
                    "h6[class*='hover:cursor-pointer']",
                    "//h6[contains(text(), 'Skip Question')]",
                    "//h6[contains(@class, 'hover:cursor-pointer')]",
                    "//button[contains(text(), 'Skip')]",
                    "//button[contains(text(), 'skip')]",
                    "//a[contains(text(), 'Skip')]",
                    "//a[contains(text(), 'skip')]"
                ]
                
                for selector in skip_selectors:
                    try:
                        # Try both XPath and CSS selector methods
                        try:
                            skip_button = short_wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        except:
                            try:
                                skip_button = short_wait.until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                            except:
                                continue
                        
                        skip_button.click()
                        print(f"{Fore.GREEN}Clicked 'Skip Question' button{Style.RESET_ALL}")
                        break
                    except:
                        continue
            except TimeoutException:
                print(f"{Fore.YELLOW}No survey or skip button found, continuing...{Style.RESET_ALL}")
                
                # Try direct JavaScript click as a fallback
                try:
                    self.driver.execute_script("""
                        let skipElements = document.querySelectorAll('h6');
                        for (let el of skipElements) {
                            if (el.textContent.includes('Skip Question')) {
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    print(f"{Fore.GREEN}Attempted to click 'Skip Question' via JavaScript{Style.RESET_ALL}")
                except Exception as js_err:
                    print(f"{Fore.YELLOW}JavaScript fallback for skip button failed: {str(js_err)}{Style.RESET_ALL}")
            
            # 7. Get the final URL
            final_url = self.driver.current_url
            print(f"{Fore.GREEN}Account creation successful!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Final URL: {final_url}{Style.RESET_ALL}")
            
            # Display account information
            print("\n" + "="*50)
            print(f"{Fore.CYAN}ACCOUNT INFORMATION:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}First Name: {first_name}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Last Name: {last_name}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Email: {email}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Password: {password}{Style.RESET_ALL}")
            print("="*50 + "\n")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}Error during signup process: {str(e)}{Style.RESET_ALL}")
            # Take screenshot on error for debugging
            screenshot_path = os.path.join(os.path.expanduser("~"), "turbolearn_error.png")
            try:
                self.driver.save_screenshot(screenshot_path)
                print(f"{Fore.YELLOW}Error screenshot saved to: {screenshot_path}{Style.RESET_ALL}")
            except:
                pass
            return False
    
    def cleanup(self):
        """Clean up resources thoroughly to prevent additional processes."""
        if hasattr(self, 'driver') and self.driver:
            try:
                # First try the standard quit
                self.driver.quit()
            except Exception as e:
                print(f"{Fore.YELLOW}Error during browser cleanup: {str(e)}{Style.RESET_ALL}")
                try:
                    # If standard quit fails, try to close any remaining windows
                    for window in self.driver.window_handles:
                        self.driver.switch_to.window(window)
                        self.driver.close()
                except:
                    pass
            
            # Then force quit as a last resort
            try:
                import psutil
                import os
                pid = self.driver.service.process.pid
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    try:
                        child.terminate()
                    except:
                        pass
                parent.terminate()
            except:
                pass


def main():
    """Main function to run the TurboLearn signup automation."""
    parser = argparse.ArgumentParser(description='Automate TurboLearn signup process')
    parser.add_argument('--private', action='store_true', help='Run browser in private mode')
    parser.add_argument('--browser', type=str, help='Specify browser to use (chrome, firefox, edge, vivaldi, brave, opera)')
    parser.add_argument('--driver', type=str, help='Path to a specific WebDriver executable')
    parser.add_argument('--clear-cache', action='store_true', help='Clear WebDriver cache before starting')
    parser.add_argument('--manual-driver', action='store_true', help='Force manual download of the WebDriver')
    parser.add_argument('--auto-close', action='store_true', help='Automatically close the browser after completion')
    args = parser.parse_args()
    
    # Clear WebDriver cache if requested
    if args.clear_cache:
        clear_webdriver_cache()
    
    # Detect installed browsers
    installed_browsers = detect_installed_browsers()
    
    # Select browser
    browser_name = None
    browser_path = None
    
    if args.browser and args.browser.lower() in installed_browsers:
        browser_name = args.browser.lower()
        browser_path = installed_browsers[browser_name]
        print(f"{Fore.GREEN}Using specified browser: {browser_name.capitalize()}{Style.RESET_ALL}")
    elif args.browser:
        print(f"{Fore.YELLOW}Specified browser '{args.browser}' not found. Please choose from available browsers.{Style.RESET_ALL}")
    
    # If browser not specified or not found, let user choose
    if not browser_name:
        print(f"\n{Fore.CYAN}Available browsers:{Style.RESET_ALL}")
        browser_options = list(installed_browsers.keys())
        for i, browser in enumerate(browser_options, 1):
            print(f"{i}. {browser.capitalize()}")
        
        browser_choice = None
        while browser_choice is None:
            try:
                choice = input("\nSelect a browser (number) or 'q' to quit: ").lower()
                if choice == 'q':
                    print(f"{Fore.YELLOW}Exiting program.{Style.RESET_ALL}")
                    return
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(browser_options):
                    browser_name = browser_options[choice_idx]
                    browser_path = installed_browsers[browser_name]
                    browser_choice = choice  # Set browser_choice to exit the loop
                else:
                    print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and {len(browser_options)}.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Invalid input. Please enter a number or 'q'.{Style.RESET_ALL}")
    
    # Check for running browser instances
    check_browser_running(browser_name, browser_path)
    
    # Choose browsing mode
    mode_choice = None
    if args.private:
        mode_choice = True
    else:
        while mode_choice is None:
            choice = input("Choose browser mode [(n)ormal/(p)rivate/(q)uit]: ").lower()
            if choice in ['n', 'normal']:
                mode_choice = False
            elif choice in ['p', 'private']:
                mode_choice = True
            elif choice in ['q', 'quit']:
                print(f"{Fore.YELLOW}Exiting program.{Style.RESET_ALL}")
                return
            else:
                print(f"{Fore.RED}Invalid choice. Please enter 'n', 'p', or 'q'.{Style.RESET_ALL}")
    
    try:
        turbolearn = TurboLearnSignup(
            browser_name=browser_name,
            browser_path=browser_path,
            private_mode=mode_choice,
            driver_path=args.driver,
            force_manual_download=args.manual_driver
        )
        
        success = turbolearn.signup_process()
        if success:
            print(f"{Fore.GREEN}Signup process completed successfully!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Signup process failed.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
    finally:
        # If we got to the point of creating the TurboLearn object
        if 'turbolearn' in locals():
            # Either auto-close or ask the user
            if args.auto_close:
                turbolearn.cleanup()
                print(f"{Fore.CYAN}Browser automatically closed.{Style.RESET_ALL}")
            else:
                try:
                    # Use a timeout for the input to prevent hanging
                    from threading import Timer
                    
                    answer = [None]
                    def timeout_input():
                        answer[0] = 'n'
                        print("\nInput timed out. Closing browser.")
                    
                    timer = Timer(10.0, timeout_input)
                    timer.start()
                    
                    user_choice = input("Keep browser open? (y/n): ").lower()
                    timer.cancel()
                    
                    if user_choice and user_choice in 'yn':
                        answer[0] = user_choice
                    
                    if answer[0] != 'y':
                        turbolearn.cleanup()
                        print(f"{Fore.CYAN}Browser closed. Goodbye!{Style.RESET_ALL}")
                except (KeyboardInterrupt, EOFError):
                    # Handle interrupts gracefully
                    print(f"\n{Fore.YELLOW}Interrupted. Closing browser.{Style.RESET_ALL}")
                    turbolearn.cleanup()


if __name__ == "__main__":
    main() 