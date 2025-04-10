#!/usr/bin/env python3
import os
import sys
import time
import json
import threading
import subprocess
import tkinter as tk
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import uuid
try:
    import customtkinter as ctk
except ImportError:
    print("CustomTkinter not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter as ctk

# Import the original script functions
try:
    from turbolearn_signup import detect_installed_browsers
    
    # Try to import TurboLearnSignup, but we need to modify it to support headless mode
    try:
        from turbolearn_signup import TurboLearnSignup as OriginalTurboLearnSignup
        
        # Create an enhanced version of TurboLearnSignup that supports headless mode and proxy
        class TurboLearnSignup(OriginalTurboLearnSignup):
            def __init__(self, browser_name=None, browser_path=None, private_mode=False, 
                        force_manual_download=False, driver_path=None, headless=False, proxy=None):
                # Store additional parameters
                self.headless = headless
                self.proxy = proxy
                
                # Call the original constructor
                super().__init__(browser_name, browser_path, private_mode, force_manual_download, driver_path)
                
            def _init_chromium_browser(self, private_mode, driver_path=None):
                """Override to add headless mode and proxy support."""
                # Get the original method
                import types
                original_method = super()._init_chromium_browser
                
                # Define a wrapper that adds our extra parameters
                def wrapper(private_mode, driver_path=None):
                    from selenium.webdriver.chrome.options import Options as ChromeOptions
                    
                    # Create options object
                    options = ChromeOptions()
                    
                    # Add standard options
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--ignore-certificate-errors")
                    options.add_argument("--disable-extensions")
                    
                    # Add headless mode if needed
                    if self.headless:
                        options.add_argument("--headless=new")
                        print("Running in headless mode")
                    
                    # Add proxy if specified
                    if self.proxy:
                        options.add_argument(f"--proxy-server={self.proxy}")
                        print(f"Using proxy: {self.proxy}")
                    
                    # Set browser binary if path is provided
                    if self.browser_path and os.path.exists(self.browser_path):
                        options.binary_location = self.browser_path
                    
                    if private_mode:
                        print("Starting browser in private mode...")
                        options.add_argument("--incognito")
                    
                    # Set up service and driver
                    from selenium.webdriver.chrome.service import Service as ChromeService
                    from selenium import webdriver
                    from webdriver_manager.chrome import ChromeDriverManager
                    
                    # Set up the service with a specific driver path or automatic download
                    if driver_path and os.path.exists(driver_path):
                        print(f"Using provided ChromeDriver at {driver_path}")
                        service = ChromeService(executable_path=driver_path)
                    elif hasattr(self, 'manual_driver_path') and self.manual_driver_path and os.path.exists(self.manual_driver_path):
                        print(f"Using manually downloaded ChromeDriver at {self.manual_driver_path}")
                        service = ChromeService(executable_path=self.manual_driver_path)
                    else:
                        # Try with automatic ChromeDriver download
                        print("Downloading appropriate ChromeDriver...")
                        service = ChromeService(ChromeDriverManager().install())
                    
                    # Initialize webdriver with error handling
                    try:
                        self.driver = webdriver.Chrome(service=service, options=options)
                        # Increase default timeout to 30 seconds
                        from selenium.webdriver.support.ui import WebDriverWait
                        self.wait = WebDriverWait(self.driver, 30)
                        print("Browser started successfully!")
                    except Exception as e:
                        error_msg = str(e)
                        print(f"Failed to initialize WebDriver: {error_msg}")
                        raise
                
                # Replace the original method with our wrapper
                return wrapper(private_mode, driver_path)
                
            # Override other browser initialization methods similarly
            def _init_firefox_browser(self, private_mode, driver_path=None):
                """Override to add headless mode and proxy support."""
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                
                options = FirefoxOptions()
                
                # Set browser binary if path is provided
                if self.browser_path and os.path.exists(self.browser_path):
                    options.binary_location = self.browser_path
                
                # Add headless mode if needed
                if self.headless:
                    options.add_argument("--headless")
                    print("Running in headless mode")
                
                # Add proxy if specified
                if self.proxy:
                    options.set_preference("network.proxy.type", 1)
                    proxy_parts = self.proxy.split(':')
                    if len(proxy_parts) >= 2:
                        options.set_preference("network.proxy.http", proxy_parts[0])
                        options.set_preference("network.proxy.http_port", int(proxy_parts[1]))
                        options.set_preference("network.proxy.ssl", proxy_parts[0])
                        options.set_preference("network.proxy.ssl_port", int(proxy_parts[1]))
                    print(f"Using proxy: {self.proxy}")
                
                if private_mode:
                    print("Starting browser in private mode...")
                    options.add_argument("-private")
                
                # Set up the service with a specific driver path or automatic download
                from selenium.webdriver.firefox.service import Service as FirefoxService
                from selenium import webdriver
                from webdriver_manager.firefox import GeckoDriverManager
                
                if driver_path and os.path.exists(driver_path):
                    print(f"Using provided GeckoDriver at {driver_path}")
                    service = FirefoxService(executable_path=driver_path)
                else:
                    # Try with automatic GeckoDriver download
                    print(f"Downloading appropriate GeckoDriver...")
                    service = FirefoxService(GeckoDriverManager().install())
                
                # Initialize webdriver with error handling
                try:
                    self.driver = webdriver.Firefox(service=service, options=options)
                    from selenium.webdriver.support.ui import WebDriverWait
                    self.wait = WebDriverWait(self.driver, 30)
                    print(f"Browser started successfully!")
                except Exception as e:
                    error_msg = str(e)
                    print(f"Failed to initialize Firefox WebDriver: {error_msg}")
                    raise
    
    except ImportError:
        # Fallback implementation if we can't import the original
        class TurboLearnSignup:
            def __init__(self, browser_name=None, browser_path=None, private_mode=False, 
                        force_manual_download=False, driver_path=None, headless=False, proxy=None):
                self.name = browser_name
                self.path = browser_path
                self.headless = headless
                self.proxy = proxy
                print("Warning: Using stub TurboLearnSignup class")
            
            def generate_random_name(self):
                import random
                first_names = ["John", "Jane", "Michael", "Sarah"]
                last_names = ["Smith", "Johnson", "Williams", "Brown"]
                return random.choice(first_names), random.choice(last_names)
                
            def get_temp_email(self):
                import random
                import string
                username = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
                return f"{username}@example.com"
                
            def generate_password(self, length=12):
                import random
                import string
                return ''.join(random.choice(string.ascii_letters + string.digits + "!@#$") for _ in range(length))
                
            def signup_process(self):
                print("Stub signup process - not actually performing signup")
                return False
                
            def cleanup(self):
                pass
                
except ImportError:
    # Define backup functions in case of import failure
    def detect_installed_browsers():
        print("Warning: Using fallback browser detection")
        import os
        browsers = {}
        # Check for Chrome in standard locations
        chrome_paths = [
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                browsers["chrome"] = path
                break
        
        if not browsers:
            browsers["chrome"] = None  # Default fallback
        return browsers
    
    # Create stub class
    class TurboLearnSignup:
        def __init__(self, browser_name=None, browser_path=None, private_mode=False, 
                    force_manual_download=False, driver_path=None, headless=False, proxy=None):
            self.name = browser_name
            self.path = browser_path
            self.headless = headless
            self.proxy = proxy
            print("Warning: Using stub TurboLearnSignup class")
        
        def generate_random_name(self):
            import random
            first_names = ["John", "Jane", "Michael", "Sarah"]
            last_names = ["Smith", "Johnson", "Williams", "Brown"]
            return random.choice(first_names), random.choice(last_names)
            
        def get_temp_email(self):
            import random
            import string
            username = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
            return f"{username}@example.com"
            
        def generate_password(self, length=12):
            import random
            import string
            return ''.join(random.choice(string.ascii_letters + string.digits + "!@#$") for _ in range(length))
            
        def signup_process(self):
            print("Stub signup process - not actually performing signup")
            return False
            
        def cleanup(self):
            pass

# Set appearance mode and color theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        self.text_widget.configure(state="normal")
        
        # Strip ANSI color codes
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_string = ansi_escape.sub('', string)
        
        # Add timestamp to each new line if not empty
        if clean_string.strip():
            from datetime import datetime
            timestamp = datetime.now().strftime("[%H:%M:%S] ")
            
            # Apply colorization to the output with emojis and timestamp
            self.text_widget.insert("end", timestamp, "timestamp")
            
            if "Clicked" in clean_string or "Found" in clean_string:
                self.text_widget.insert("end", "✅ ", "emoji")
                self.text_widget.insert("end", clean_string, "success")
            elif "successful" in clean_string or "successfully" in clean_string:
                self.text_widget.insert("end", "🎉 ", "emoji")
                self.text_widget.insert("end", clean_string, "success")
            elif "Error" in clean_string or "Failed" in clean_string or "Could not" in clean_string:
                self.text_widget.insert("end", "❌ ", "emoji")
                self.text_widget.insert("end", clean_string, "error")
            elif "Waiting" in clean_string or "Looking" in clean_string:
                self.text_widget.insert("end", "🔍 ", "emoji")
                self.text_widget.insert("end", clean_string, "info")
            elif "Starting" in clean_string:
                self.text_widget.insert("end", "🚀 ", "emoji")
                self.text_widget.insert("end", clean_string, "starting")
            elif "progress" in clean_string.lower() or "processing" in clean_string.lower():
                self.text_widget.insert("end", "⏳ ", "emoji")
                self.text_widget.insert("end", clean_string, "progress")
            elif "browser" in clean_string.lower():
                self.text_widget.insert("end", "🌐 ", "emoji")
                self.text_widget.insert("end", clean_string, "browser")
            elif "download" in clean_string.lower():
                self.text_widget.insert("end", "📥 ", "emoji")
                self.text_widget.insert("end", clean_string, "download")
            elif "password" in clean_string.lower():
                self.text_widget.insert("end", "🔑 ", "emoji")
                self.text_widget.insert("end", clean_string, "password")
            elif "email" in clean_string.lower():
                self.text_widget.insert("end", "📧 ", "emoji")
                self.text_widget.insert("end", clean_string, "email")
            elif "=" in clean_string and "=" == clean_string[0]:
                # Section divider
                self.text_widget.insert("end", clean_string, "divider")
            elif "initializing" in clean_string.lower() or "detected" in clean_string.lower():
                # Handle initialization messages
                self.text_widget.insert("end", clean_string, "info")
            elif "navigating" in clean_string.lower() or "filling" in clean_string.lower():
                # Handle navigation and form filling
                self.text_widget.insert("end", clean_string, "browser")
            elif "account information" in clean_string.lower():
                # Handle account info headers
                self.text_widget.insert("end", clean_string, "info")
            else:
                self.text_widget.insert("end", clean_string)
                
            # Update status bar with latest activity
            if hasattr(self.text_widget, 'update_status_bar'):
                self.text_widget.update_status_bar(clean_string)
            
        self.text_widget.configure(state="disabled")
        self.text_widget.see("end")
        
    def flush(self):
        self.buffer = ""

class AccountInfo:
    def __init__(self):
        self.data_dir = os.path.join(os.path.expanduser("~"), ".turbolearn")
        self.accounts_file = os.path.join(self.data_dir, "accounts.json")
        
        # Create directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Initialize or load accounts
        self.accounts = self.load_accounts()
        
    def load_accounts(self):
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, "r") as file:
                    return json.load(file)
            except:
                pass
                
        # Default structure if file doesn't exist or error
        return {
            "accounts": [],
            "statistics": {"success": 0, "failed": 0},
            "settings": {"auth_password": "turbolearn123"},
            "favorites": [],  # Store favorite account IDs
            "tags": {},       # Map tag names to colors
            "account_tags": {}  # Map account IDs to list of tags
        }
        
    def save_accounts(self):
        with open(self.accounts_file, "w") as file:
            json.dump(self.accounts, file)
            
    def add_account(self, first_name, last_name, email, password, url, success=True):
        # Create unique ID for the account
        account_id = str(uuid.uuid4())
        
        # Create account object
        account = {
            "id": account_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "url": url,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Success" if success else "Failed"
        }
        
        # Add to accounts list
        self.accounts["accounts"].append(account)
        
        # Update statistics
        if success:
            self.accounts["statistics"]["success"] += 1
        else:
            self.accounts["statistics"]["failed"] += 1
            
        # Save to file
        self.save_accounts()
        
        return account
        
    def get_accounts(self, favorites_first=True):
        accounts = self.accounts["accounts"]
        
        if favorites_first and "favorites" in self.accounts:
            # Sort with favorites at the top
            favorites = self.accounts["favorites"]
            sorted_accounts = []
            
            # Add favorites first
            for account in accounts:
                if account["id"] in favorites:
                    sorted_accounts.append(account)
            
            # Add non-favorites
            for account in accounts:
                if account["id"] not in favorites:
                    sorted_accounts.append(account)
                    
            return sorted_accounts
        
        return accounts
    
    def get_statistics(self):
        return self.accounts["statistics"]
        
    def get_auth_password(self):
        if "settings" in self.accounts and "auth_password" in self.accounts["settings"]:
            return self.accounts["settings"]["auth_password"]
        return "turbolearn123"  # Default password
        
    def set_auth_password(self, new_password):
        if "settings" not in self.accounts:
            self.accounts["settings"] = {}
            
        self.accounts["settings"]["auth_password"] = new_password
        self.save_accounts()
        
    def toggle_favorite(self, account_id):
        """Toggle favorite status for an account"""
        if "favorites" not in self.accounts:
            self.accounts["favorites"] = []
            
        if account_id in self.accounts["favorites"]:
            self.accounts["favorites"].remove(account_id)
            is_favorite = False
        else:
            self.accounts["favorites"].append(account_id)
            is_favorite = True
            
        self.save_accounts()
        return is_favorite
        
    def is_favorite(self, account_id):
        """Check if an account is favorite"""
        if "favorites" not in self.accounts:
            return False
        return account_id in self.accounts["favorites"]
    
    def add_tag(self, tag_name, tag_color="#3a7ebf"):
        """Add a new tag with color"""
        if "tags" not in self.accounts:
            self.accounts["tags"] = {}
            
        self.accounts["tags"][tag_name] = tag_color
        self.save_accounts()
        
    def remove_tag(self, tag_name):
        """Remove a tag and all its assignments"""
        if "tags" not in self.accounts or tag_name not in self.accounts["tags"]:
            return False
            
        # Remove the tag
        del self.accounts["tags"][tag_name]
        
        # Remove tag assignments from accounts
        if "account_tags" in self.accounts:
            for account_id in list(self.accounts["account_tags"].keys()):
                if tag_name in self.accounts["account_tags"][account_id]:
                    self.accounts["account_tags"][account_id].remove(tag_name)
                    
                # Clean up empty tag lists
                if not self.accounts["account_tags"][account_id]:
                    del self.accounts["account_tags"][account_id]
                    
        self.save_accounts()
        return True
        
    def get_tags(self):
        """Get all available tags with colors"""
        if "tags" not in self.accounts:
            self.accounts["tags"] = {}
        return self.accounts["tags"]
        
    def add_account_tag(self, account_id, tag_name):
        """Add a tag to an account"""
        # Make sure the tag exists
        if "tags" not in self.accounts or tag_name not in self.accounts["tags"]:
            return False
            
        # Initialize account_tags if needed
        if "account_tags" not in self.accounts:
            self.accounts["account_tags"] = {}
            
        # Initialize tags for this account if needed
        if account_id not in self.accounts["account_tags"]:
            self.accounts["account_tags"][account_id] = []
            
        # Add the tag if not already there
        if tag_name not in self.accounts["account_tags"][account_id]:
            self.accounts["account_tags"][account_id].append(tag_name)
            self.save_accounts()
            
        return True
        
    def remove_account_tag(self, account_id, tag_name):
        """Remove a tag from an account"""
        if "account_tags" not in self.accounts or account_id not in self.accounts["account_tags"]:
            return False
            
        if tag_name in self.accounts["account_tags"][account_id]:
            self.accounts["account_tags"][account_id].remove(tag_name)
            
            # Clean up empty tag lists
            if not self.accounts["account_tags"][account_id]:
                del self.accounts["account_tags"][account_id]
                
            self.save_accounts()
            return True
            
        return False
        
    def get_account_tags(self, account_id):
        """Get all tags for an account"""
        if "account_tags" not in self.accounts or account_id not in self.accounts["account_tags"]:
            return []
            
        return self.accounts["account_tags"][account_id]
        
    def get_accounts_by_tag(self, tag_name):
        """Get all accounts with a specific tag"""
        result = []
        
        if "account_tags" not in self.accounts:
            return result
            
        # Find all accounts with this tag
        for account_id, tags in self.accounts["account_tags"].items():
            if tag_name in tags:
                # Find the account by ID
                for account in self.accounts["accounts"]:
                    if account["id"] == account_id:
                        result.append(account)
                        break
                        
        return result
    
    def delete_account(self, account_id):
        """Delete an account and all its references"""
        # Remove from accounts list
        for i, account in enumerate(self.accounts["accounts"]):
            if account["id"] == account_id:
                del self.accounts["accounts"][i]
                
                # Update statistics
                if account["status"] == "Success":
                    self.accounts["statistics"]["success"] -= 1
                else:
                    self.accounts["statistics"]["failed"] -= 1
                    
                # Remove from favorites
                if "favorites" in self.accounts and account_id in self.accounts["favorites"]:
                    self.accounts["favorites"].remove(account_id)
                    
                # Remove from tags
                if "account_tags" in self.accounts and account_id in self.accounts["account_tags"]:
                    del self.accounts["account_tags"][account_id]
                    
                self.save_accounts()
                return True
                
        return False

# Create a function to detect installed drivers
def detect_installed_drivers():
    """Detect WebDrivers installed in the drivers directory."""
    drivers = {}
    drivers_dir = os.path.join(os.getcwd(), "drivers")
    
    # Check if drivers directory exists
    if not os.path.exists(drivers_dir):
        return drivers
    
    # Chrome driver
    chrome_driver_path = os.path.join(drivers_dir, "chrome", "chromedriver-win64", "chromedriver.exe")
    if os.path.exists(chrome_driver_path):
        drivers["chrome"] = chrome_driver_path
    
    # Firefox driver
    firefox_driver_path = os.path.join(drivers_dir, "firefox", "geckodriver.exe")
    if os.path.exists(firefox_driver_path):
        drivers["firefox"] = firefox_driver_path
    
    # Edge driver
    edge_driver_path = os.path.join(drivers_dir, "edge", "msedgedriver.exe")
    if os.path.exists(edge_driver_path):
        drivers["edge"] = edge_driver_path
    
    return drivers

class TurboLearnGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Define color themes with blue accent instead of purple
        self.colors = {
            "light": {
                "bg": "#ffffff",
                "fg": "#18181b",
                "bg_secondary": "#f1f5f9",
                "border": "#e2e8f0",
                "accent": "#3a7ebf",  # Changed from #6923ff to blue
                "accent_foreground": "#f8fafc",
                "success": "#22c55e",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "icon": "#64748b"
            },
            "dark": {
                "bg": "#18181b",
                "fg": "#f8fafc",
                "bg_secondary": "#27272a",
                "border": "#3f3f46",
                "accent": "#3a7ebf",  # Changed from #6923ff to blue
                "accent_foreground": "#f8fafc",
                "success": "#22c55e",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "icon": "#94a3b8"
            }
        }
        
        # Create app icon if it doesn't exist
        self.create_app_icon()
        
        # Continue with the rest of initialization
        
        # Configure window
        self.title("TurboLearn Signup Automation")
        self.geometry("1200x800")
        self.minsize(900, 700)
        
        # Initialize account tracker
        self.account_info = AccountInfo()
        
        # Authentication settings
        self.is_authenticated = False
        self.auth_password = self.account_info.get_auth_password()  # Load password from storage
        
        # Initialize browsers
        try:
            self.browsers = detect_installed_browsers()
            if not self.browsers:
                self.browsers = {"chrome": None}  # Default fallback
        except Exception as e:
            print(f"Error detecting browsers: {str(e)}")
            self.browsers = {"chrome": None}  # Default fallback
            
        # Initialize available drivers
        self.available_drivers = detect_installed_drivers()
        
        # Variables
        self.selected_browser = tk.StringVar(value=list(self.browsers.keys())[0] if self.browsers else "chrome")
        self.private_mode = tk.BooleanVar(value=False)
        self.auto_close = tk.BooleanVar(value=True)
        self.is_running = False
        self.process_thread = None
        
        # Additional feature variables
        self.silent_mode = tk.BooleanVar(value=True)
        self.use_existing_driver = tk.BooleanVar(value=False)
        self.selected_driver = tk.StringVar(value="")
        self.headless_mode = tk.BooleanVar(value=False)
        self.batch_mode = tk.BooleanVar(value=False)
        self.batch_count = tk.IntVar(value=1)
        self.use_proxy = tk.BooleanVar(value=False)
        self.proxy_address = tk.StringVar(value="")
        
        # Create main containers
        self.create_tabs()
        
    def create_tabs(self):
        # Create tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create tabs
        self.tab_automation = self.tabview.add("Automation")
        self.tab_dashboard = self.tabview.add("Dashboard")
        self.tab_visualization = self.tabview.add("Analytics")
        self.tab_scheduler = self.tabview.add("Scheduler")
        self.tab_settings = self.tabview.add("Settings")
        
        # Setup each tab
        self.setup_automation_tab()
        self.setup_dashboard_tab()
        self.setup_visualization_tab()
        self.setup_scheduler_tab()
        self.setup_settings_tab()
        
    def setup_automation_tab(self):
        # Create left and right frames
        left_frame = ctk.CTkFrame(self.tab_automation)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        right_frame = ctk.CTkFrame(self.tab_automation)
        right_frame.pack(side="right", fill="both", expand=False, padx=10, pady=10, ipadx=10, ipady=10, anchor="n")
        
        # Add scrolling to right frame for all the controls
        right_scroll = ctk.CTkScrollableFrame(right_frame, width=250)
        right_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Left frame - Console without header
        console_container = ctk.CTkFrame(left_frame, fg_color=("gray90", "gray20"), corner_radius=10)
        console_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Search frame above console
        search_frame = ctk.CTkFrame(console_container, fg_color="transparent")
        search_frame.pack(fill="x", padx=8, pady=(8, 0))
        
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Search in console...",
            width=200,
            textvariable=self.search_var
        )
        search_entry.pack(side="left", padx=(0, 5))
        
        search_button = ctk.CTkButton(
            search_frame,
            text="Find 🔍",
            width=80,
            command=self.search_console,
            fg_color="#3b82f6",
            hover_color="#2563eb"
        )
        search_button.pack(side="left", padx=5)
        
        clear_search_button = ctk.CTkButton(
            search_frame,
            text="Clear 🧹",
            width=80,
            command=self.clear_search,
            fg_color="#ef4444",
            hover_color="#dc2626"
        )
        clear_search_button.pack(side="left", padx=5)
        
        self.search_results_label = ctk.CTkLabel(
            search_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.search_results_label.pack(side="left", padx=5)
        
        # Bind Enter key to search
        search_entry.bind("<Return>", lambda event: self.search_console())
        
        # Customized console with improved appearance
        self.console = ctk.CTkTextbox(
            console_container, 
            width=700, 
            height=600, 
            font=ctk.CTkFont(family="Cascadia Code", size=12),
            fg_color=("gray95", "gray15"),  # Light/dark mode backgrounds
            text_color=("gray10", "gray90"),  # Light/dark mode text color
            corner_radius=6,
            border_width=1,
            border_color=("gray75", "gray35")  # Light/dark mode border
        )
        self.console.pack(fill="both", expand=True, padx=8, pady=8)
        self.console.configure(state="disabled")
        
        # Enhanced color tags for different message types
        self.console.tag_config("success", foreground="#10b981")  # Green
        self.console.tag_config("error", foreground="#ef4444")    # Red
        self.console.tag_config("info", foreground="#3b82f6")     # Blue
        self.console.tag_config("starting", foreground="#f59e0b") # Amber
        self.console.tag_config("progress", foreground="#8b5cf6") # Purple
        self.console.tag_config("browser", foreground="#06b6d4")  # Cyan
        self.console.tag_config("download", foreground="#ec4899") # Pink
        self.console.tag_config("password", foreground="#6366f1") # Indigo
        self.console.tag_config("email", foreground="#14b8a6")    # Teal
        self.console.tag_config("emoji", foreground="#f97316")    # Orange
        self.console.tag_config("divider", foreground="#6b7280")  # Gray
        self.console.tag_config("timestamp", foreground="#9ca3af") # Gray-400 for timestamps
        self.console.tag_config("search_result", background="#fef3c7") # Highlight for search results
        
        # Add a function to update the status bar
        def update_status_bar(text):
            status = "Idle"
            if "Starting" in text:
                status = "Starting browser"
            elif "Navigating" in text:
                status = "Navigating website"
            elif "Filling" in text:
                status = "Filling form"
            elif "Looking" in text or "Waiting" in text:
                status = "Waiting for elements"
            elif "Clicked" in text:
                status = "Interacting with page"
            elif "successful" in text or "successfully" in text:
                status = "Operation completed"
            elif "Error" in text or "Failed" in text:
                status = "Error occurred"
            
            self.status_label.configure(text=f"Status: {status}")
        
        # Attach the function to the console for the RedirectText class to use
        self.console.update_status_bar = update_status_bar
        
        # Create a text redirect
        self.text_redirect = RedirectText(self.console)
        
        # Status bar at the bottom
        status_bar = ctk.CTkFrame(console_container, height=30, fg_color=("gray85", "gray25"))
        status_bar.pack(fill="x", padx=8, pady=(0, 8))
        
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Status: Idle",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Control buttons frame
        console_controls = ctk.CTkFrame(left_frame)
        console_controls.pack(fill="x", pady=10)
        
        # Clear console button with icon
        clear_console_button = ctk.CTkButton(
            console_controls,
            text="Clear Console 🧹",
            command=self.clear_console,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#3b82f6",  # Blue
            hover_color="#2563eb"  # Darker blue
        )
        clear_console_button.pack(side="left", padx=10)
        
        # Copy to clipboard button
        copy_console_button = ctk.CTkButton(
            console_controls,
            text="Copy Output 📋",
            command=self.copy_console_content,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#10b981",  # Green
            hover_color="#059669"  # Darker green
        )
        copy_console_button.pack(side="left", padx=10)
        
        # Save log button
        save_log_button = ctk.CTkButton(
            console_controls,
            text="Save Log 💾",
            command=self.save_console_log,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#8b5cf6",  # Purple
            hover_color="#7c3aed"  # Darker purple
        )
        save_log_button.pack(side="left", padx=10)
        
        # Add sample text to console when starting up
        self.console.configure(state="normal")
        welcome_message = "🚀 TurboLearn Console initialized and ready!\n"
        welcome_message += "✨ Welcome to TurboLearn Signup Automation ✨\n\n"
        welcome_message += "Select options and click 'Start Automation' to begin.\n"
        self.console.insert("end", welcome_message)
        self.console.configure(state="disabled")
        
        # Right frame - Controls
        controls_label = ctk.CTkLabel(right_scroll, text="Controls", font=ctk.CTkFont(size=16, weight="bold"))
        controls_label.pack(pady=(0, 10))
        
        # Browser selection
        browser_frame = ctk.CTkFrame(right_scroll)
        browser_frame.pack(fill="x", padx=10, pady=10)
        
        browser_label = ctk.CTkLabel(browser_frame, text="Browser:")
        browser_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        # Available browsers
        for browser in self.browsers:
            browser_option = ctk.CTkRadioButton(
                browser_frame,
                text=browser.capitalize(),
                variable=self.selected_browser,
                value=browser
            )
            browser_option.pack(anchor="w", padx=20, pady=2)
            
        # WebDriver Selection - New Section
        driver_selection_frame = ctk.CTkFrame(right_scroll)
        driver_selection_frame.pack(fill="x", padx=10, pady=10)
        
        driver_label = ctk.CTkLabel(
            driver_selection_frame, 
            text="WebDriver Selection", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        driver_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # WebDriver selection radio buttons
        self.driver_selection = tk.StringVar(value="auto")
        
        auto_driver = ctk.CTkRadioButton(
            driver_selection_frame,
            text="Auto-download WebDriver",
            variable=self.driver_selection,
            value="auto",
            command=self.toggle_driver_selection
        )
        auto_driver.pack(anchor="w", padx=20, pady=2)
        
        # Create container for driver options
        self.driver_options_frame = ctk.CTkFrame(driver_selection_frame, fg_color="transparent")
        self.driver_options_frame.pack(fill="x", padx=10, pady=5)
        
        # Add local drivers option if we have them
        if self.available_drivers:
            local_driver = ctk.CTkRadioButton(
                driver_selection_frame,
                text="Use local WebDrivers",
                variable=self.driver_selection,
                value="local",
                command=self.toggle_driver_selection
            )
            local_driver.pack(anchor="w", padx=20, pady=2)
            
            # Create a frame for driver selection dropdown
            self.local_drivers_frame = ctk.CTkFrame(self.driver_options_frame)
            
            driver_dropdown_label = ctk.CTkLabel(
                self.local_drivers_frame,
                text="Select WebDriver:",
                anchor="w"
            )
            driver_dropdown_label.pack(anchor="w", padx=10, pady=(5, 0))
            
            # Create a dropdown (combobox) for the drivers
            driver_options = list(self.available_drivers.keys())
            driver_dropdown = ctk.CTkComboBox(
                self.local_drivers_frame,
                values=driver_options,
                variable=self.selected_driver,
                width=200,
                command=self.update_driver_path
            )
            if driver_options:
                driver_dropdown.set(driver_options[0])
            driver_dropdown.pack(padx=10, pady=5)
        
        # Custom driver option
        custom_driver = ctk.CTkRadioButton(
            driver_selection_frame,
            text="Select custom WebDriver",
            variable=self.driver_selection,
            value="custom",
            command=self.toggle_driver_selection
        )
        custom_driver.pack(anchor="w", padx=20, pady=2)
        
        # Create a frame for custom driver selection
        self.custom_driver_frame = ctk.CTkFrame(self.driver_options_frame)
        
        select_driver_button = ctk.CTkButton(
            self.custom_driver_frame,
            text="Browse for WebDriver",
            command=self.select_driver_file
        )
        select_driver_button.pack(pady=5)
        
        self.driver_path_label = ctk.CTkLabel(
            self.custom_driver_frame,
            text="No file selected",
            wraplength=200
        )
        self.driver_path_label.pack(pady=5)
        
        # Initially hide driver frames
        if hasattr(self, 'local_drivers_frame'):
            self.local_drivers_frame.pack_forget()
        self.custom_driver_frame.pack_forget()
        
        # Mode selection
        mode_frame = ctk.CTkFrame(right_scroll)
        mode_frame.pack(fill="x", padx=10, pady=10)
        
        mode_label = ctk.CTkLabel(
            mode_frame, 
            text="Browser Options", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        mode_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        private_mode_switch = ctk.CTkSwitch(
            mode_frame, 
            text="Private Mode", 
            variable=self.private_mode
        )
        private_mode_switch.pack(anchor="w", padx=10, pady=5)
        
        # Add Headless Mode Option (new)
        headless_mode_switch = ctk.CTkSwitch(
            mode_frame, 
            text="Headless Mode (Faster)", 
            variable=self.headless_mode
        )
        headless_mode_switch.pack(anchor="w", padx=10, pady=5)
        
        auto_close_switch = ctk.CTkSwitch(
            mode_frame, 
            text="Auto Close Browser", 
            variable=self.auto_close
        )
        auto_close_switch.pack(anchor="w", padx=10, pady=5)
        
        # Add silent mode option
        silent_mode_switch = ctk.CTkSwitch(
            mode_frame, 
            text="Silent Mode (Hide Errors)", 
            variable=self.silent_mode
        )
        silent_mode_switch.pack(anchor="w", padx=10, pady=5)
        
        # Add Batch mode (new)
        batch_frame = ctk.CTkFrame(right_scroll)
        batch_frame.pack(fill="x", padx=10, pady=10)
        
        batch_label = ctk.CTkLabel(
            batch_frame, 
            text="Batch Processing", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        batch_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        batch_mode_switch = ctk.CTkSwitch(
            batch_frame, 
            text="Enable Batch Mode", 
            variable=self.batch_mode,
            command=self.toggle_batch_settings
        )
        batch_mode_switch.pack(anchor="w", padx=10, pady=5)
        
        self.batch_settings_frame = ctk.CTkFrame(batch_frame)
        self.batch_settings_frame.pack(fill="x", padx=10, pady=5)
        
        batch_count_label = ctk.CTkLabel(self.batch_settings_frame, text=f"Number of Accounts: {self.batch_count.get()}")
        batch_count_label.pack(anchor="w", padx=10, pady=5)
        
        def update_batch_count(value):
            self.batch_count.set(int(value))
            batch_count_label.configure(text=f"Number of Accounts: {self.batch_count.get()}")
        
        batch_count_slider = ctk.CTkSlider(
            self.batch_settings_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            command=update_batch_count
        )
        batch_count_slider.set(1)
        batch_count_slider.pack(fill="x", padx=10, pady=5)
        
        # Initially hide batch settings
        self.batch_settings_frame.pack_forget()
        
        # Add Proxy Support (new)
        proxy_frame = ctk.CTkFrame(right_scroll)
        proxy_frame.pack(fill="x", padx=10, pady=10)
        
        proxy_label = ctk.CTkLabel(
            proxy_frame, 
            text="Proxy Settings", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        proxy_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        proxy_switch = ctk.CTkSwitch(
            proxy_frame, 
            text="Use Proxy", 
            variable=self.use_proxy,
            command=self.toggle_proxy_settings
        )
        proxy_switch.pack(anchor="w", padx=10, pady=5)
        
        self.proxy_settings_frame = ctk.CTkFrame(proxy_frame)
        self.proxy_settings_frame.pack(fill="x", padx=10, pady=5)
        
        proxy_address_label = ctk.CTkLabel(
            self.proxy_settings_frame, 
            text="Proxy Address:"
        )
        proxy_address_label.pack(anchor="w", padx=10, pady=5)
        
        proxy_format_label = ctk.CTkLabel(
            self.proxy_settings_frame, 
            text="Format: host:port or user:pass@host:port",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        proxy_format_label.pack(anchor="w", padx=10, pady=(0, 5))
        
        proxy_entry = ctk.CTkEntry(
            self.proxy_settings_frame,
            textvariable=self.proxy_address,
            placeholder_text="127.0.0.1:8080"
        )
        proxy_entry.pack(fill="x", padx=10, pady=5)
        
        # Initially hide proxy settings
        self.proxy_settings_frame.pack_forget()
        
        # Progress indicators
        self.progress_frame = ctk.CTkFrame(right_scroll)
        self.progress_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Status: Ready")
        self.progress_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        
        # Start button
        self.start_button = ctk.CTkButton(
            right_scroll, 
            text="Start Automation", 
            command=self.start_automation,
            height=40,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_button.pack(fill="x", padx=10, pady=10)
        
        # Stop button
        self.stop_button = ctk.CTkButton(
            right_scroll, 
            text="Stop", 
            command=self.stop_automation,
            height=40,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_button.pack(fill="x", padx=10, pady=10)
        
    def toggle_batch_settings(self):
        if self.batch_mode.get():
            self.batch_settings_frame.pack(fill="x", padx=10, pady=5)
        else:
            self.batch_settings_frame.pack_forget()
            
    def toggle_proxy_settings(self):
        if self.use_proxy.get():
            self.proxy_settings_frame.pack(fill="x", padx=10, pady=5)
        else:
            self.proxy_settings_frame.pack_forget()
        
    def toggle_driver_selection(self):
        if self.driver_selection.get() == "local":
            self.local_drivers_frame.pack(fill="x", padx=10, pady=5)
            self.custom_driver_frame.pack_forget()
        elif self.driver_selection.get() == "custom":
            self.custom_driver_frame.pack(fill="x", padx=10, pady=5)
            self.local_drivers_frame.pack_forget()
        else:
            self.local_drivers_frame.pack_forget()
            self.custom_driver_frame.pack_forget()
            
    def select_driver_file(self):
        try:
            from tkinter import filedialog
            
            file_path = filedialog.askopenfilename(
                title="Select WebDriver",
                filetypes=[
                    ("Executable files", "*.exe"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                self.driver_path.set(file_path)
                self.driver_path_label.configure(text=os.path.basename(file_path))
        except Exception as e:
            self.show_message("Error", f"Could not select file: {str(e)}")
            
    def clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        
        # Add a "console cleared" message
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        self.console.insert("end", timestamp, "timestamp")
        self.console.insert("end", "🧹 Console cleared and ready for new output!\n", "info")
        self.console.configure(state="disabled")
        
        # Update status
        self.status_label.configure(text="Status: Idle")
        
    def copy_console_content(self):
        """Copy console content to clipboard"""
        content = self.console.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)
        
        # Show notification in console
        self.console.configure(state="normal")
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        self.console.insert("end", timestamp, "timestamp")
        self.console.insert("end", "📋 Console content copied to clipboard!\n", "success")
        self.console.configure(state="disabled")
        self.console.see("end")
        
    def save_console_log(self):
        """Save console output to a log file"""
        import os
        from datetime import datetime
        from tkinter import filedialog
        
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"turbolearn_log_{timestamp}.txt"
        
        # Get save location from user
        filename = filedialog.asksaveasfilename(
            initialdir=os.path.expanduser("~"),
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if filename:
            # Get console content
            content = self.console.get("1.0", "end-1c")
            
            # Write to file
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                
                # Show success notification
                self.console.configure(state="normal")
                timestamp = datetime.now().strftime("[%H:%M:%S] ")
                self.console.insert("end", timestamp, "timestamp")
                self.console.insert("end", f"💾 Log saved successfully to: {filename}\n", "success")
                self.console.configure(state="disabled")
                self.console.see("end")
            except Exception as e:
                # Show error notification
                self.console.configure(state="normal")
                timestamp = datetime.now().strftime("[%H:%M:%S] ")
                self.console.insert("end", timestamp, "timestamp")
                self.console.insert("end", f"❌ Error saving log: {str(e)}\n", "error")
                self.console.configure(state="disabled")
                self.console.see("end")
    
    def search_console(self):
        """Search text in the console"""
        query = self.search_var.get().strip()
        if not query:
            return
            
        # Clear previous highlights
        self.clear_search(update_ui=False)
        
        # Get console content
        content = self.console.get("1.0", "end-1c")
        
        # Find all occurrences (case insensitive)
        import re
        matches = list(re.finditer(re.escape(query), content, re.IGNORECASE))
        
        # Highlight matches
        for match in matches:
            start_index = match.start()
            end_index = match.end()
            
            # Convert byte offset to line and column
            start_line = content[:start_index].count("\n") + 1
            start_col = start_index - content[:start_index].rfind("\n") - 1 if "\n" in content[:start_index] else start_index
            
            end_line = content[:end_index].count("\n") + 1
            end_col = end_index - content[:end_index].rfind("\n") - 1 if "\n" in content[:end_index] else end_index
            
            # Apply highlight tag
            self.console.tag_add("search_result", f"{start_line}.{start_col}", f"{end_line}.{end_col}")
        
        # Update results count
        count = len(matches)
        if count > 0:
            self.search_results_label.configure(text=f"{count} result{'s' if count != 1 else ''}")
            
            # Scroll to first match
            if matches:
                start_index = matches[0].start()
                start_line = content[:start_index].count("\n") + 1
                self.console.see(f"{start_line}.0")
        else:
            self.search_results_label.configure(text="No results")
    
    def clear_search(self, update_ui=True):
        """Clear search highlights"""
        self.console.tag_remove("search_result", "1.0", "end")
        if update_ui:
            self.search_var.set("")
            self.search_results_label.configure(text="")
    
    def setup_dashboard_tab(self):
        # Create frame for dashboard
        self.dashboard_frame = ctk.CTkFrame(self.tab_dashboard)
        self.dashboard_frame.pack(fill="both", expand=True)

        # Handle authentication if enabled
        if hasattr(self, 'dashboard_login_var') and not self.dashboard_login_var.get():
            # Skip authentication if disabled
            self.is_authenticated = True  # Set authenticated since login is disabled
            self.create_dashboard_content()
        else:
            # Create authentication panel
            self.is_authenticated = False  # Not authenticated until login
            self.create_auth_panel()
    
    def create_auth_panel(self):
        """Create an authentication panel for dashboard"""
        self.auth_frame = ctk.CTkFrame(self.dashboard_frame)
        self.auth_frame.pack(expand=True, fill="both")
        
        # Add padlock icon or similar visual
        icon_label = ctk.CTkLabel(
            self.auth_frame,
            text="🔒",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(40, 10))
        
        # Add login message
        info_label = ctk.CTkLabel(
            self.auth_frame,
            text="Authentication Required",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        info_label.pack(pady=10)
        
        password_frame = ctk.CTkFrame(self.auth_frame)
        password_frame.pack(pady=20, padx=20)
        
        password_label = ctk.CTkLabel(
            password_frame,
            text="Password:",
            font=ctk.CTkFont(size=14)
        )
        password_label.pack(side="left", padx=(0, 10))
        
        self.password_var = tk.StringVar()
        password_entry = ctk.CTkEntry(
            password_frame,
            textvariable=self.password_var,
            show="*",
            width=200,
            height=30,
            placeholder_text="turbolearn123"  # Default password placeholder
        )
        password_entry.pack(side="left")
        
        # Add login button
        login_button = ctk.CTkButton(
            self.auth_frame,
            text="Login",
            command=self.authenticate,
            width=150,
            fg_color="blue",
            hover_color="darkblue"
        )
        login_button.pack(pady=20)
        
        # Add public mode info
        public_info = ctk.CTkLabel(
            self.auth_frame,
            text="TurboLearn is open source but account data is private.\nOnly authenticated users can access their generated accounts.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="center"
        )
        public_info.pack(pady=30)
    
    def authenticate(self):
        """Authenticate user to view dashboard data"""
        # Skip authentication if dashboard login is disabled
        if hasattr(self, 'dashboard_login_var') and not self.dashboard_login_var.get():
            self.is_authenticated = True
            for widget in self.dashboard_frame.winfo_children():
                widget.destroy()
            self.create_dashboard_content()
            return
            
        entered_password = self.password_var.get()
        
        # Get stored password or use default
        stored_password = self.account_info.get_auth_password()
        if stored_password is None:
            stored_password = "turbolearn123"  # Default password
        
        if entered_password == stored_password:
            self.is_authenticated = True
            
            # Clear password entry
            self.password_var.set("")
            
            # Destroy authentication panel
            for widget in self.dashboard_frame.winfo_children():
                widget.destroy()
                
            # Create dashboard content
            self.create_dashboard_content()
        else:
            self.show_message("Error", "Invalid password. Please try again.")
    
    def create_dashboard_content(self):
        """Show the actual dashboard content after authentication"""
        # Add toolbar frame with actions
        toolbar_frame = ctk.CTkFrame(self.dashboard_frame)
        toolbar_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Left side of toolbar
        left_actions = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        left_actions.pack(side="left", fill="x", expand=True)
        
        # Search frame
        search_frame = ctk.CTkFrame(left_actions, fg_color="transparent")
        search_frame.pack(side="left", padx=5, fill="x", expand=True)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_accounts())
        
        search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Search accounts...",
            textvariable=self.search_var,
            width=200
        )
        search_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Clear search button
        clear_button = ctk.CTkButton(
            search_frame,
            text="✕",
            width=30,
            command=lambda: self.search_var.set("")
        )
        clear_button.pack(side="left", padx=5)
        
        # Right side of toolbar
        right_actions = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        right_actions.pack(side="right")
        
        # Refresh button
        refresh_button = ctk.CTkButton(
            right_actions,
            text="Refresh",
            command=self.refresh_dashboard,
            width=80
        )
        refresh_button.pack(side="left", padx=5)
        
        # Export button
        export_button = ctk.CTkButton(
            right_actions,
            text="Export CSV",
            command=self.export_accounts_to_csv,
            width=80
        )
        export_button.pack(side="left", padx=5)
        
        # Create split view for table and detail view
        self.dashboard_split = ctk.CTkFrame(self.dashboard_frame)
        self.dashboard_split.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Table frame - left side
        self.table_frame = ctk.CTkFrame(self.dashboard_split)
        self.table_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=0)
        
        # Detail frame - right side (initially hidden)
        self.detail_frame = ctk.CTkFrame(self.dashboard_split)
        
        # Add quick access bar at the bottom
        self.create_quick_access_bar()
        
        # Table headers
        headers = ["First Name", "Last Name", "Email", "Created", "Status", "Actions"]
        header_frame = ctk.CTkFrame(self.table_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Configure grid
        for i, header in enumerate(headers):
            lbl = ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            header_frame.grid_columnconfigure(i, weight=1)
        
        # Create scrollable frame for data
        self.account_scroll = ctk.CTkScrollableFrame(self.table_frame)
        self.account_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Load accounts
        self.refresh_dashboard()
        self.account_detail = None  # Track the currently selected account
        
    def filter_accounts(self, *args):
        """Filter accounts based on search query"""
        query = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        
        # If no search query, just refresh normally
        if not query:
            self.refresh_dashboard()
            return
            
        # Clear existing widgets in scrollable frame
        for widget in self.account_scroll.winfo_children():
            widget.destroy()
            
        # Get accounts
        accounts = self.account_info.get_accounts()
        filtered_accounts = []
        
        # Filter based on search query
        for account in accounts:
            # Search in name, email, date
            search_text = (
                f"{account['first_name']} {account['last_name']} "
                f"{account['email']} {account['created_at']} {account['status']}"
            ).lower()
            
            if query in search_text:
                filtered_accounts.append(account)
        
        # Add filtered accounts to table
        self.display_filtered_accounts(filtered_accounts)
    
    def display_filtered_accounts(self, accounts):
        """Display filtered list of accounts"""
        # If no accounts match, show message
        if not accounts:
            no_results = ctk.CTkLabel(
                self.account_scroll,
                text="No accounts found matching your search",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            no_results.pack(pady=30)
            return
            
        # Display accounts
        for i, account in enumerate(accounts):
            # Create colored background based on status
            bg_color = "#E8F5E9" if account["status"] == "Success" else "#FFEBEE"
            row_frame = ctk.CTkFrame(self.account_scroll)
            row_frame.pack(fill="x", padx=5, pady=2)
            
            # Add data
            ctk.CTkLabel(row_frame, text=account["first_name"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            ctk.CTkLabel(row_frame, text=account["last_name"]).grid(row=0, column=1, padx=5, pady=5, sticky="w")
            ctk.CTkLabel(row_frame, text=account["email"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
            ctk.CTkLabel(row_frame, text=account["created_at"]).grid(row=0, column=3, padx=5, pady=5, sticky="w")
            
            # Status with color
            status_color = "green" if account["status"] == "Success" else "red"
            status_label = ctk.CTkLabel(row_frame, text=account["status"])
            status_label.configure(text_color=status_color)
            status_label.grid(row=0, column=4, padx=5, pady=5, sticky="w")
            
            # Action buttons
            actions_frame = ctk.CTkFrame(row_frame)
            actions_frame.grid(row=0, column=5, padx=5, pady=5, sticky="e")
            
            # Open in browser button
            if account["status"] == "Success" and "url" in account and account["url"]:
                open_button = ctk.CTkButton(
                    actions_frame,
                    text="Open",
                    command=lambda acc=account: self.open_account(acc["url"]),
                    width=60,
                    height=25
                )
                open_button.pack(side="left", padx=5)
            
            # Copy info button
            copy_button = ctk.CTkButton(
                actions_frame,
                text="Copy",
                command=lambda acc=account: self.copy_account_info(acc),
                width=60,
                height=25
            )
            copy_button.pack(side="left", padx=5)
            
            # Configure grid
            for j in range(6):
                row_frame.grid_columnconfigure(j, weight=1)
                
            # Add hover effect
            def on_enter(e, rf=row_frame):
                rf.configure(fg_color=("gray85", "gray25"))
            
            def on_leave(e, rf=row_frame):
                rf.configure(fg_color=("gray75", "gray30"))
            
            # Make the row clickable to show details
            def show_detail(e, acc=account):
                self.show_account_details(acc)
                
            row_frame.bind("<Enter>", on_enter)
            row_frame.bind("<Leave>", on_leave)
            row_frame.bind("<Button-1>", show_detail)
            
            # Make all child labels clickable too
            for child in row_frame.winfo_children():
                child.bind("<Button-1>", lambda e, acc=account: self.show_account_details(acc))
    
    def setup_settings_tab(self):
        """Setup the settings tab"""
        # Create frame for settings
        self.settings_frame = ctk.CTkFrame(self.tab_settings)
        self.settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Settings title
        settings_title = ctk.CTkLabel(
            self.settings_frame,
            text="Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        settings_title.pack(pady=10)
        
        # Create scrollable frame for settings
        settings_scroll = ctk.CTkScrollableFrame(self.settings_frame)
        settings_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Theme section
        theme_frame = ctk.CTkFrame(settings_scroll)
        theme_frame.pack(fill="x", padx=10, pady=10)
        
        theme_label = ctk.CTkLabel(
            theme_frame,
            text="Appearance",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        theme_label.pack(anchor="w", padx=10, pady=10)
        
        # Appearance mode
        appearance_label = ctk.CTkLabel(theme_frame, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=10, pady=5)
        
        appearance_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode
        )
        appearance_menu.set(ctk.get_appearance_mode())
        appearance_menu.pack(anchor="w", padx=20, pady=5)
        
        # UI Scaling
        scaling_label = ctk.CTkLabel(theme_frame, text="UI Scaling:")
        scaling_label.pack(anchor="w", padx=10, pady=5)
        
        ui_scale_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event
        )
        ui_scale_menu.set("100%")
        ui_scale_menu.pack(anchor="w", padx=20, pady=5)
        
        # Dashboard Login Toggle
        dashboard_frame = ctk.CTkFrame(settings_scroll)
        dashboard_frame.pack(fill="x", padx=10, pady=10)
        
        dashboard_label = ctk.CTkLabel(
            dashboard_frame,
            text="Dashboard Login",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        dashboard_label.pack(anchor="w", padx=10, pady=10)
        
        self.dashboard_login_var = tk.BooleanVar(value=False)
        
        login_switch = ctk.CTkSwitch(
            dashboard_frame,
            text="",
            variable=self.dashboard_login_var,
            command=self.toggle_dashboard_login,
            onvalue=True,
            offvalue=False
        )
        login_switch.pack(side="left", padx=10, pady=10)
        
        # Shortcut section
        shortcut_frame = ctk.CTkFrame(settings_scroll)
        shortcut_frame.pack(fill="x", padx=10, pady=10)
        
        shortcut_label = ctk.CTkLabel(
            shortcut_frame,
            text="Desktop Shortcut",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        shortcut_label.pack(anchor="w", padx=10, pady=10)
        
        create_shortcut_button = ctk.CTkButton(
            shortcut_frame,
            text="Create Desktop Shortcut",
            command=self.create_desktop_shortcut
        )
        create_shortcut_button.pack(anchor="w", padx=20, pady=10)
        
        # Security settings
        security_frame = ctk.CTkFrame(settings_scroll)
        security_frame.pack(fill="x", padx=10, pady=10)
        
        security_label = ctk.CTkLabel(
            security_frame,
            text="Security",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        security_label.pack(anchor="w", padx=10, pady=10)
        
        # Password change section
        password_frame = ctk.CTkFrame(security_frame)
        password_frame.pack(fill="x", padx=10, pady=10)
        
        # Current password
        current_pass_frame = ctk.CTkFrame(password_frame)
        current_pass_frame.pack(fill="x", padx=10, pady=5)
        
        current_pass_label = ctk.CTkLabel(
            current_pass_frame,
            text="Current Password:",
            width=150
        )
        current_pass_label.pack(side="left", padx=(0, 10))
        
        self.current_password_var = tk.StringVar()
        current_pass_entry = ctk.CTkEntry(
            current_pass_frame,
            textvariable=self.current_password_var,
            show="*",
            width=200,
            height=30
        )
        current_pass_entry.pack(side="left")
        
        # New password
        new_pass_frame = ctk.CTkFrame(password_frame)
        new_pass_frame.pack(fill="x", padx=10, pady=5)
        
        new_pass_label = ctk.CTkLabel(
            new_pass_frame,
            text="New Password:",
            width=150
        )
        new_pass_label.pack(side="left", padx=(0, 10))
        
        self.new_password_var = tk.StringVar()
        new_pass_entry = ctk.CTkEntry(
            new_pass_frame,
            textvariable=self.new_password_var,
            show="*",
            width=200,
            height=30
        )
        new_pass_entry.pack(side="left")
        
        # Confirm password
        confirm_pass_frame = ctk.CTkFrame(password_frame)
        confirm_pass_frame.pack(fill="x", padx=10, pady=5)
        
        confirm_pass_label = ctk.CTkLabel(
            confirm_pass_frame,
            text="Confirm Password:",
            width=150
        )
        confirm_pass_label.pack(side="left", padx=(0, 10))
        
        self.confirm_password_var = tk.StringVar()
        confirm_pass_entry = ctk.CTkEntry(
            confirm_pass_frame,
            textvariable=self.confirm_password_var,
            show="*",
            width=200,
            height=30
        )
        confirm_pass_entry.pack(side="left")
        
        # Change password button
        change_pass_button = ctk.CTkButton(
            password_frame,
            text="Change Password",
            command=self.change_password,
            fg_color="blue",
            hover_color="darkblue"
        )
        change_pass_button.pack(anchor="w", padx=10, pady=10)
    
    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        
    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        
    def change_password(self):
        """Handle password change request"""
        current_password = self.current_password_var.get()
        new_password = self.new_password_var.get()
        confirm_password = self.confirm_password_var.get()
        
        # Validate inputs
        if current_password != self.auth_password:
            self.show_message("Error", "Current password is incorrect")
            return
            
        if not new_password:
            self.show_message("Error", "New password cannot be empty")
            return
            
        if new_password != confirm_password:
            self.show_message("Error", "New passwords do not match")
            return
            
        # Update the password
        self.auth_password = new_password
        self.account_info.set_auth_password(new_password)
        
        # Clear the password fields
        self.current_password_var.set("")
        self.new_password_var.set("")
        self.confirm_password_var.set("")
        
        self.show_message("Success", "Password updated successfully")
        
    def export_data(self):
        # Export account data as JSON
        try:
            from tkinter import filedialog
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Account Data"
            )
            
            if file_path:
                with open(file_path, "w") as f:
                    json.dump(self.account_info.accounts, f, indent=4)
                
                self.show_message("Export Successful", "Account data exported successfully.")
        except Exception as e:
            self.show_message("Export Failed", f"Error exporting data: {str(e)}")
            
    def clear_data(self):
        # Show confirmation dialog
        confirm = tk.messagebox.askyesno(
            "Confirm Clear Data", 
            "Are you sure you want to clear all account data? This action cannot be undone."
        )
        
        if confirm:
            # Reset data
            self.account_info.accounts = {"accounts": [], "statistics": {"success": 0, "failed": 0}, "settings": {"auth_password": "turbolearn123"}}
            self.account_info.save_accounts()
            
            # Refresh UI
            self.refresh_dashboard()
            self.refresh_visualization()
            
            self.show_message("Data Cleared", "All account data has been cleared.")
            
    def show_message(self, title, message):
        tk.messagebox.showinfo(title, message)
        
    def start_automation(self):
        if self.is_running:
            return
            
        # Get selected options
        browser = self.selected_browser.get()
        private = self.private_mode.get()
        auto_close = self.auto_close.get()
        
        # Validate browser
        if browser not in self.browsers:
            self.show_message("Error", f"Selected browser '{browser}' is not available.")
            return
            
        # Disable start button and enable stop button
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
        # Update status
        self.is_running = True
        self.progress_label.configure(text="Status: Initializing...")
        
        # Start automation in a separate thread
        self.process_thread = threading.Thread(
            target=self._run_automation_process,
            args=(browser, private, auto_close)
        )
        self.process_thread.daemon = True
        self.process_thread.start()
        
    def _run_automation_process(self, browser, private, auto_close):
        # Redirect stdout to capture output
        old_stdout = sys.stdout
        sys.stdout = self.text_redirect
        
        # Update progress
        self.update_progress(0.1, "Starting browser...")
        
        # Set custom driver path if specified
        custom_driver_path = None
        if hasattr(self, 'driver_selection'):
            driver_selection = self.driver_selection.get()
            
            if driver_selection == "local" and self.selected_driver.get() in self.available_drivers:
                custom_driver_path = self.available_drivers[self.selected_driver.get()]
                print(f"Using local WebDriver: {custom_driver_path}")
            elif driver_selection == "custom" and self.driver_path.get():
                custom_driver_path = self.driver_path.get()
                print(f"Using custom WebDriver: {custom_driver_path}")
            else:
                print("Using automatic WebDriver download")
        elif self.use_existing_driver.get() and self.driver_path.get():
            # Backward compatibility
            custom_driver_path = self.driver_path.get()
            print(f"Using custom WebDriver from: {custom_driver_path}")
        
        # Determine batch count
        batch_count = self.batch_count.get() if self.batch_mode.get() else 1
        
        # Proxy settings
        proxy = self.proxy_address.get() if self.use_proxy.get() else None
        
        # Run in batch mode if enabled
        for batch_index in range(batch_count):
            if not self.is_running:
                break
                
            if batch_count > 1:
                self.update_progress((batch_index / batch_count) * 0.9, f"Processing account {batch_index+1}/{batch_count}")
                print(f"\n{'='*30}")
                print(f"Starting account creation {batch_index+1} of {batch_count}")
                print(f"{'='*30}\n")
            
            # Create TurboLearnSignup instance for this batch
            try:
                # Clear console if in silent mode for first batch only
                if self.silent_mode.get() and batch_index == 0:
                    self.clear_console()
                    
                # Prepare browser options including headless and proxy if needed
                browser_options = {
                    "browser_name": browser,
                    "browser_path": self.browsers[browser],
                    "private_mode": private,
                    "force_manual_download": False,
                    "driver_path": custom_driver_path,
                    "headless": self.headless_mode.get(),
                    "proxy": proxy
                }
                
                turbolearn = TurboLearnSignup(**browser_options)
                
                # Capture variables for account info
                first_name = last_name = email = password = final_url = None
                success = False
                
                # Run the signup process
                if batch_count == 1:
                    self.update_progress(0.3, "Navigating to site...")
                
                # Monkey patch methods to capture variables
                original_generate_name = turbolearn.generate_random_name
                original_get_email = turbolearn.get_temp_email
                original_generate_password = turbolearn.generate_password
                
                def patched_generate_name():
                    nonlocal first_name, last_name
                    first_name, last_name = original_generate_name()
                    return first_name, last_name
                    
                def patched_get_email():
                    nonlocal email
                    email = original_get_email()
                    return email
                    
                def patched_generate_password(length=12):
                    nonlocal password
                    password = original_generate_password(length)
                    return password
                    
                # Apply patches
                turbolearn.generate_random_name = patched_generate_name
                turbolearn.get_temp_email = patched_get_email
                turbolearn.generate_password = patched_generate_password
                
                # Add error filtering for silent mode
                if self.silent_mode.get():
                    original_print = print
                    
                    def filtered_print(*args, **kwargs):
                        text = " ".join(str(arg) for arg in args)
                        if not any(err in text for err in [
                            "ERROR:", "Failed to", "Could not", 
                            "Max retries exceeded", "No connection",
                            "ConnectionResetError", "ConnectionError",
                            "WebDriverException"
                        ]):
                            original_print(*args, **kwargs)
                    
                    # Apply patch to built-in print
                    import builtins
                    builtins.print = filtered_print
                
                # Run signup process
                if batch_count == 1:
                    self.update_progress(0.5, "Filling form...")
                try:
                    success = turbolearn.signup_process()
                except Exception as e:
                    print(f"Error during signup: {str(e)}")
                    success = False
                
                # Restore original print if needed
                if self.silent_mode.get():
                    builtins.print = original_print
                
                # Get final URL
                if hasattr(turbolearn, 'driver'):
                    try:
                        final_url = turbolearn.driver.current_url
                    except:
                        final_url = "Unknown"
                    
                # Update progress for single account mode
                if batch_count == 1:
                    self.update_progress(0.9, "Completing process...")
                
                # Add account info if we have the required data
                if first_name and last_name and email and password:
                    self.account_info.add_account(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        password=password,
                        url=final_url,
                        success=success
                    )
                
                # Update database and visualizations after each account
                self.update_ui()
                    
                # Auto-close for all accounts except the last one
                if auto_close or batch_index < batch_count - 1:
                    if hasattr(turbolearn, 'driver') and turbolearn.driver:
                        turbolearn.cleanup()
                elif batch_index == batch_count - 1 and not auto_close:
                    # Ask user if they want to keep the browser open for the last batch
                    def ask_keep_open():
                        keep_open = tk.messagebox.askyesno(
                            "Keep Browser", 
                            "Keep browser open?"
                        )
                        if not keep_open and hasattr(turbolearn, 'driver') and turbolearn.driver:
                            turbolearn.cleanup()
                    
                    # Schedule on main thread
                    self.after(100, ask_keep_open)
                    
            except Exception as e:
                print(f"Fatal error in batch {batch_index+1}: {str(e)}")
                if batch_count == 1:
                    self.update_progress(1.0, "Error")
        
        # Complete progress at the end of all batches
        self.update_progress(1.0, "Completed")
        
        # Reset UI state
        self.after(100, self.reset_ui_state)
        # Restore stdout
        sys.stdout = old_stdout
        
    def update_progress(self, value, status_text):
        # Schedule UI update on main thread
        self.after(10, lambda: self._update_progress_ui(value, status_text))
        
    def _update_progress_ui(self, value, status_text):
        self.progress_bar.set(value)
        self.progress_label.configure(text=f"Status: {status_text}")
        
    def update_ui(self):
        # Schedule UI updates on main thread
        self.after(100, self.refresh_dashboard)
        self.after(100, self.refresh_visualization)
        
    def reset_ui_state(self):
        self.is_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
    def stop_automation(self):
        if not self.is_running:
            return
            
        # Show confirmation
        confirm = tk.messagebox.askyesno(
            "Confirm Stop", 
            "Are you sure you want to stop the automation process?"
        )
        
        if confirm:
            # Setting is_running to False will cause the process to terminate
            # at the next safe opportunity
            self.is_running = False
            self.progress_label.configure(text="Status: Stopping...")
            
            # We can't directly terminate the thread, but we can try to
            # cause the browser to close
            try:
                # This will run on main thread
                from turbolearn_signup import detect_running_browser_processes
                processes = detect_running_browser_processes(self.selected_browser.get())
                
                import psutil
                for pid in processes:
                    try:
                        process = psutil.Process(pid)
                        process.terminate()
                    except:
                        pass
            except:
                pass

    # Add a new method to update the driver path based on selection
    def update_driver_path(self, selection):
        if selection in self.available_drivers:
            driver_path = self.available_drivers[selection]
            self.driver_path.set(driver_path)
            self.driver_path_label.configure(text=f"Selected: {os.path.basename(driver_path)}")

    def create_desktop_shortcut(self):
        """Create desktop shortcut to launch the application"""
        try:
            import winshell
            import win32com.client
            from win32com.shell import shell, shellcon
            import os
            
            # Get desktop path
            desktop = winshell.desktop()
            
            # Create shortcut path
            shortcut_path = os.path.join(desktop, "TurboLearn Crack.lnk")
            
            # Get application path
            target = sys.executable
            
            # Get or create icon
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if not os.path.exists(icon_path):
                icon_path = self.create_app_icon()
            
            # Create shell link
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
            shortcut.Arguments = os.path.abspath(__file__)
            
            # Use the icon if it exists, otherwise use the executable
            if icon_path and os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
            else:
                shortcut.IconLocation = target
            
            # Save shortcut
            shortcut.save()
            
            self.show_message("Success", f"Desktop shortcut created at: {shortcut_path}")
        except ImportError as e:
            # Handle missing modules
            missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
            self.show_message("Error", f"Failed to create shortcut: No module named '{missing_module}'\n\nPlease run: pip install {missing_module}")
        except Exception as e:
            # Handle other errors
            self.show_message("Error", f"Failed to create shortcut: {str(e)}")

    def toggle_dashboard_login(self):
        # Toggle the dashboard login requirement
        is_enabled = self.dashboard_login_var.get()
        
        # Clear the dashboard frame content
        for widget in self.dashboard_frame.winfo_children():
            widget.destroy()
            
        if is_enabled:
            # If login is enabled, show auth panel
            self.create_auth_panel()
            self.show_message("Success", "Dashboard login enabled. Authentication is now required.")
        else:
            # If login is disabled, show dashboard content directly
            self.is_authenticated = True
            self.create_dashboard_content()
            self.show_message("Info", "Dashboard login disabled. Authentication is now bypassed.")

    def create_app_icon(self):
        """Create an application icon file if it doesn't exist"""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            
            # If icon already exists, don't recreate it
            if os.path.exists(icon_path):
                return icon_path
                
            # Check if PIL is installed
            try:
                from PIL import Image, ImageDraw
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
                from PIL import Image, ImageDraw
                
            # Create a base image (64x64) with transparent background
            img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw a blue circle for the background
            draw.ellipse((4, 4, 60, 60), fill=(58, 126, 191))  # #3a7ebf in RGB
            
            # Draw a stylized "T" in white
            draw.rectangle((20, 15, 44, 22), fill=(255, 255, 255))
            draw.rectangle((28, 22, 36, 48), fill=(255, 255, 255))
            
            # Save as .ico file
            img.save(icon_path, format='ICO')
            return icon_path
            
        except Exception as e:
            print(f"Error creating icon: {str(e)}")
            return None

    def export_accounts_to_csv(self):
        """Export accounts to CSV file"""
        try:
            import csv
            from tkinter import filedialog
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Account Data as CSV"
            )
            
            if not file_path:
                return
                
            accounts = self.account_info.get_accounts()
                
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                # Define CSV fields
                fieldnames = ["first_name", "last_name", "email", "password", "url", "created_at", "status"]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write account data
                for account in accounts:
                    # Create a filtered dict with only the fields we want
                    row = {field: account.get(field, "") for field in fieldnames}
                    writer.writerow(row)
                
            self.show_message("Export Successful", f"{len(accounts)} accounts exported to CSV successfully.")
        except Exception as e:
            self.show_message("Export Failed", f"Error exporting data: {str(e)}")
            print(f"CSV export error: {str(e)}")
            
    def create_quick_access_bar(self):
        """Create a quick access bar at the bottom of the dashboard"""
        quick_bar = ctk.CTkFrame(self.dashboard_frame)
        quick_bar.pack(fill="x", padx=10, pady=5, side="bottom")
        
        # Add quick buttons
        buttons = [
            ("New Account", lambda: self.tabview.set("Automation"), "➕"),
            ("Export CSV", lambda: self.export_accounts_to_csv(), "📄"),
            ("Check Updates", self.check_for_updates, "🔄"),
            ("Test Proxy", self.show_proxy_tester, "🌐")
        ]
        
        for text, command, icon in buttons:
            btn = ctk.CTkButton(
                quick_bar,
                text=f"{icon} {text}",
                command=command,
                height=30
            )
            btn.pack(side="left", padx=5, pady=5, fill="x", expand=True)
            
    def check_for_updates(self):
        """Check GitHub for updates to the application"""
        try:
            import urllib.request
            import json
            
            # Create status window
            status_window = ctk.CTkToplevel(self)
            status_window.title("Update Check")
            status_window.geometry("400x200")
            status_window.transient(self)
            status_window.grab_set()
            
            # Add loading indicator
            status_label = ctk.CTkLabel(
                status_window,
                text="Checking for updates...",
                font=ctk.CTkFont(size=16)
            )
            status_label.pack(pady=20)
            
            progress = ctk.CTkProgressBar(status_window)
            progress.pack(padx=20, pady=10, fill="x")
            progress.start()
            
            # Function to check for updates in background
            def check_update_thread():
                try:
                    # Current version (example: 1.0.0)
                    current_version = "1.0.0"
                    
                    # GitHub API URL for latest release
                    url = "https://api.github.com/repos/Yetemgeta-B/Turbolearn/releases/latest"
                    
                    # Set up request with user agent
                    req = urllib.request.Request(
                        url,
                        headers={'User-Agent': 'TurboLearn Update Checker'}
                    )
                    
                    # Make the request
                    with urllib.request.urlopen(req, timeout=5) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        
                    # Get the latest version (remove 'v' prefix if present)
                    latest_version = data['tag_name'].lstrip('v')
                    release_notes = data['body']
                    download_url = data['html_url']
                    
                    # Compare versions
                    if latest_version > current_version:
                        # Update the UI with the results
                        status_window.after(0, lambda: update_ui(
                            f"New version available: {latest_version}",
                            True,
                            latest_version,
                            release_notes,
                            download_url
                        ))
                    else:
                        # No update needed
                        status_window.after(0, lambda: update_ui(
                            f"You have the latest version: {current_version}",
                            False
                        ))
                        
                except Exception as e:
                    # Handle errors
                    status_window.after(0, lambda: update_ui(
                        f"Error checking for updates: {str(e)}",
                        False
                    ))
            
            # Function to update the UI with results
            def update_ui(message, update_available, version=None, notes=None, url=None):
                # Stop progress bar and update status
                progress.stop()
                status_label.configure(text=message)
                
                if update_available:
                    # Show update details
                    notes_frame = ctk.CTkScrollableFrame(status_window, height=80)
                    notes_frame.pack(padx=20, pady=10, fill="x")
                    
                    notes_label = ctk.CTkLabel(
                        notes_frame,
                        text=notes,
                        wraplength=350,
                        justify="left"
                    )
                    notes_label.pack(padx=10, pady=10, fill="both")
                    
                    # Add download button
                    download_button = ctk.CTkButton(
                        status_window,
                        text="Download Update",
                        command=lambda: self.open_url(url)
                    )
                    download_button.pack(pady=10)
                else:
                    # Add close button
                    close_button = ctk.CTkButton(
                        status_window,
                        text="Close",
                        command=status_window.destroy
                    )
                    close_button.pack(pady=20)
            
            # Start the check in a separate thread
            import threading
            update_thread = threading.Thread(target=check_update_thread)
            update_thread.daemon = True
            update_thread.start()
            
        except Exception as e:
            self.show_message("Error", f"Failed to check for updates: {str(e)}")
            
    def show_proxy_tester(self):
        """Show proxy testing dialog"""
        proxy_window = ctk.CTkToplevel(self)
        proxy_window.title("Proxy Tester")
        proxy_window.geometry("500x400")
        proxy_window.transient(self)
        proxy_window.grab_set()
        
        # Header
        header_label = ctk.CTkLabel(
            proxy_window,
            text="Test Proxy Connection",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.pack(pady=10)
        
        # Proxy input
        input_frame = ctk.CTkFrame(proxy_window)
        input_frame.pack(padx=20, pady=10, fill="x")
        
        proxy_label = ctk.CTkLabel(input_frame, text="Proxy URL:")
        proxy_label.pack(side="left", padx=10)
        
        proxy_var = tk.StringVar()
        proxy_entry = ctk.CTkEntry(input_frame, textvariable=proxy_var, width=300)
        proxy_entry.pack(side="left", padx=10, fill="x", expand=True)
        
        # Format helper text
        format_label = ctk.CTkLabel(
            proxy_window,
            text="Format: http://username:password@host:port or http://host:port",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        format_label.pack(pady=(0, 10))
        
        # Test sites
        sites_frame = ctk.CTkFrame(proxy_window)
        sites_frame.pack(padx=20, pady=10, fill="x")
        
        sites_label = ctk.CTkLabel(sites_frame, text="Test Sites:")
        sites_label.pack(anchor="w", padx=10, pady=5)
        
        test_sites = [
            ("Google", "https://www.google.com"),
            ("Cloudflare", "https://www.cloudflare.com"),
            ("GitHub", "https://api.github.com"),
            ("Custom URL", "")
        ]
        
        site_var = tk.StringVar(value=test_sites[0][1])
        
        for i, (name, url) in enumerate(test_sites):
            site_rb = ctk.CTkRadioButton(
                sites_frame,
                text=name,
                variable=site_var,
                value=url,
                command=lambda: custom_entry.configure(state="normal" if site_var.get() == "" else "disabled")
            )
            site_rb.pack(anchor="w", padx=20, pady=2)
        
        # Custom URL entry
        custom_frame = ctk.CTkFrame(sites_frame)
        custom_frame.pack(padx=20, pady=5, fill="x")
        
        custom_var = tk.StringVar()
        custom_entry = ctk.CTkEntry(custom_frame, textvariable=custom_var, placeholder_text="Enter custom URL", state="disabled")
        custom_entry.pack(fill="x")
        
        # Results frame
        results_frame = ctk.CTkFrame(proxy_window)
        results_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        results_label = ctk.CTkLabel(
            results_frame,
            text="Test Results:",
            font=ctk.CTkFont(weight="bold")
        )
        results_label.pack(anchor="w", padx=10, pady=5)
        
        results_text = ctk.CTkTextbox(results_frame)
        results_text.pack(padx=10, pady=5, fill="both", expand=True)
        results_text.configure(state="disabled")
        
        # Test button
        test_button = ctk.CTkButton(
            proxy_window,
            text="Test Connection",
            command=lambda: self.test_proxy_connection(
                proxy_var.get(),
                site_var.get() if site_var.get() != "" else custom_var.get(),
                results_text
            )
        )
        test_button.pack(pady=10)
        
    def test_proxy_connection(self, proxy_url, test_url, results_text):
        """Test a proxy connection to a specified URL"""
        if not proxy_url:
            self.show_message("Error", "Please enter a proxy URL")
            return
            
        if not test_url:
            self.show_message("Error", "Please enter a test URL")
            return
            
        # Enable text widget for writing results
        results_text.configure(state="normal")
        results_text.delete("0.0", "end")
        results_text.insert("0.0", f"Testing proxy: {proxy_url}\nTarget: {test_url}\n\n")
        
        # Run test in background thread
        def test_thread():
            try:
                import requests
                import time
                
                start_time = time.time()
                
                # Set up proxy
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }
                
                # Make the request with a timeout
                response = requests.get(test_url, proxies=proxies, timeout=10)
                
                # Calculate time
                elapsed_time = time.time() - start_time
                
                # Show results
                if response.status_code == 200:
                    results = (
                        f"✅ Success! Connected in {elapsed_time:.2f} seconds\n\n"
                        f"Status Code: {response.status_code}\n"
                        f"Response Size: {len(response.content)} bytes\n\n"
                        f"Your IP as seen by server: "
                    )
                    
                    # Try to get the IP address
                    try:
                        ip_response = requests.get("https://api.ipify.org", proxies=proxies, timeout=5)
                        results += ip_response.text
                    except:
                        results += "Could not determine"
                        
                else:
                    results = (
                        f"⚠️ Warning: Got response code {response.status_code} in {elapsed_time:.2f} seconds\n\n"
                        f"This might indicate an issue with the proxy or the target site.\n"
                        f"Response Size: {len(response.content)} bytes"
                    )
                    
                # Update UI in main thread
                self.after(0, lambda: update_results(results, "success" if response.status_code == 200 else "warning"))
                
            except Exception as e:
                # Handle error
                error_message = (
                    f"❌ Error: Could not connect using the proxy\n\n"
                    f"Error details: {str(e)}\n\n"
                    f"Possible causes:\n"
                    f"- Incorrect proxy format\n"
                    f"- Proxy server is down or unreachable\n"
                    f"- Authentication required but not provided\n"
                    f"- Network connectivity issues"
                )
                
                # Update UI in main thread
                self.after(0, lambda: update_results(error_message, "error"))
        
        # Function to update results in the UI thread
        def update_results(message, status):
            # Add colored status indicator
            if status == "success":
                results_text.insert("end", message, ("success",))
                results_text.tag_configure("success", foreground="green")
            elif status == "warning":
                results_text.insert("end", message, ("warning",))
                results_text.tag_configure("warning", foreground="orange")
            else:
                results_text.insert("end", message, ("error",))
                results_text.tag_configure("error", foreground="red")
                
            results_text.configure(state="disabled")
        
        # Start the test thread
        import threading
        test_thread = threading.Thread(target=test_thread)
        test_thread.daemon = True
        test_thread.start()
        
        # Show initial message
        results_text.insert("end", "Testing connection, please wait...\n\n")
        results_text.configure(state="disabled")
    
    def open_url(self, url):
        """Open any URL in the default browser"""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            self.show_message("Error", f"Could not open URL: {str(e)}")

if __name__ == "__main__":
    # Check if matplotlib is installed
    try:
        import matplotlib
    except ImportError:
        print("Matplotlib not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
        
    # Start the application
    app = TurboLearnGUI()
    
    # Initialize the scheduler check
    app.after(1000, app.check_scheduled_tasks)
    
    # Run the main loop
    app.mainloop() 