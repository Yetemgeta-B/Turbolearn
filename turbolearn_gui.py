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
        self.file_path = "account_data.json"
        self.accounts = self.load_accounts()
        self.backup_dir = "backups"
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
    def load_accounts(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except:
                return {"accounts": [], "statistics": {"success": 0, "failed": 0}, "settings": {"auth_password": "turbolearn123"}}
        else:
            return {"accounts": [], "statistics": {"success": 0, "failed": 0}, "settings": {"auth_password": "turbolearn123"}}
            
    def save_accounts(self):
        with open(self.file_path, "w") as f:
            json.dump(self.accounts, f)
        # Create backup after saving
        self.create_backup()
            
    def add_account(self, first_name, last_name, email, password, url, success=True):
        account = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "url": url,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Success" if success else "Failed",
            "used": False,
            "last_used": None
        }
        self.accounts["accounts"].append(account)
        
        # Update statistics
        if success:
            self.accounts["statistics"]["success"] += 1
        else:
            self.accounts["statistics"]["failed"] += 1
            
        self.save_accounts()
        
        # Schedule dashboard refresh on the main thread
        if hasattr(self, 'root'):
            self.root.after(0, self.refresh_dashboard)
        
    def get_accounts(self):
        return self.accounts["accounts"]
        
    def get_statistics(self):
        return self.accounts["statistics"]
        
    def get_auth_password(self):
        """Get the stored authentication password"""
        if "settings" not in self.accounts:
            self.accounts["settings"] = {"auth_password": "turbolearn123"}
            self.save_accounts()
        return self.accounts["settings"].get("auth_password", "turbolearn123")
        
    def set_auth_password(self, new_password):
        """Update the authentication password"""
        if "settings" not in self.accounts:
            self.accounts["settings"] = {}
        self.accounts["settings"]["auth_password"] = new_password
        self.save_accounts()
        
    def create_backup(self):
        """Create a backup of the account data"""
        if not os.path.exists(self.file_path):
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"accounts_backup_{timestamp}.json")
        
        try:
            import shutil
            shutil.copy2(self.file_path, backup_path)
            # Keep only the last 10 backups
            self.cleanup_old_backups()
            return backup_path
        except Exception as e:
            print(f"Backup failed: {str(e)}")
            return None
            
    def cleanup_old_backups(self):
        """Keep only the 10 most recent backups"""
        try:
            backups = [os.path.join(self.backup_dir, f) for f in os.listdir(self.backup_dir) 
                    if f.startswith("accounts_backup_") and f.endswith(".json")]
            backups.sort(reverse=True)  # Sort newest first
            
            # Remove older backups beyond the 10 most recent
            if len(backups) > 10:
                for old_backup in backups[10:]:
                    os.remove(old_backup)
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")
            
    def restore_from_backup(self, backup_path):
        """Restore account data from a backup file"""
        if not os.path.exists(backup_path):
            return False
            
        try:
            with open(backup_path, "r") as f:
                backup_data = json.load(f)
                
            # Validate backup data structure
            if not isinstance(backup_data, dict) or "accounts" not in backup_data:
                return False
                
            # Create a backup of current data before restoring
            current_backup = self.create_backup()
            
            # Restore from backup
            self.accounts = backup_data
            with open(self.file_path, "w") as f:
                json.dump(self.accounts, f)
                
            return True
        except Exception as e:
            print(f"Restore failed: {str(e)}")
            return False
            
    def get_available_backups(self):
        """Get a list of available backup files"""
        try:
            backups = [f for f in os.listdir(self.backup_dir) 
                    if f.startswith("accounts_backup_") and f.endswith(".json")]
            backups.sort(reverse=True)  # Sort newest first
            
            result = []
            for backup in backups:
                # Extract timestamp from filename
                timestamp = backup.replace("accounts_backup_", "").replace(".json", "")
                # Format for display
                date_time = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                formatted_date = date_time.strftime("%Y-%m-%d %H:%M:%S")
                
                backup_path = os.path.join(self.backup_dir, backup)
                file_size = os.path.getsize(backup_path)
                
                result.append({
                    "filename": backup,
                    "path": backup_path,
                    "timestamp": formatted_date,
                    "size": f"{file_size/1024:.1f} KB"
                })
                
            return result
        except Exception as e:
            print(f"Failed to get backups: {str(e)}")
            return []
            
    def export_to_cloud(self, cloud_service="dropbox"):
        """Export account data to cloud storage (placeholder function)"""
        # This would be implemented with appropriate cloud service API
        return False
        
    def import_from_cloud(self, cloud_service="dropbox"):
        """Import account data from cloud storage (placeholder function)"""
        # This would be implemented with appropriate cloud service API
        return False
        
    def mark_account_used(self, account_email, used=True):
        """Mark an account as used or unused"""
        for account in self.accounts["accounts"]:
            if account["email"] == account_email:
                account["used"] = used
                account["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if used else account.get("last_used")
                self.save_accounts()
                return True
        return False
        
    def batch_action(self, emails, action):
        """Perform an action on multiple accounts
        Actions: delete, mark_used, mark_unused, export"""
        results = {"success": 0, "failed": 0}
        
        if action == "delete":
            # Find accounts to remove
            to_remove = []
            for i, account in enumerate(self.accounts["accounts"]):
                if account["email"] in emails:
                    to_remove.append(i)
                    
                    # Update statistics
                    if account["status"] == "Success":
                        self.accounts["statistics"]["success"] -= 1
                    else:
                        self.accounts["statistics"]["failed"] -= 1
                    
                    results["success"] += 1
            
            # Remove accounts in reverse order to avoid index issues
            for i in sorted(to_remove, reverse=True):
                self.accounts["accounts"].pop(i)
                
        elif action in ["mark_used", "mark_unused"]:
            used_state = action == "mark_used"
            for account in self.accounts["accounts"]:
                if account["email"] in emails:
                    account["used"] = used_state
                    if used_state:
                        account["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    results["success"] += 1
        
        # Save changes
        self.save_accounts()
        return results

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
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)  # Reduced padding
        
        # Create tabs
        self.tab_home = self.tabview.add("Home")
        self.tab_automation = self.tabview.add("Automation")
        self.tab_dashboard = self.tabview.add("Dashboard")
        self.tab_visualization = self.tabview.add("Analytics")
        self.tab_settings = self.tabview.add("Settings")
        
        # Reduce the vertical space in the dashboard tab
        self.tab_dashboard.configure(fg_color="transparent")
        
        # Setup tabs
        self.setup_home_tab()
        self.setup_automation_tab()
        self.setup_dashboard_tab()
        self.setup_visualization_tab()
        self.setup_settings_tab()
        
        # Set default tab
        self.tabview.set("Home")
        
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
            self.create_dashboard_content()
        else:
            # Create authentication panel
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
        # Create split view
        dashboard_split = ctk.CTkFrame(self.dashboard_frame)
        dashboard_split.pack(fill="both", expand=True, padx=10, pady=5)  # Reduced pady from 10 to 5
        
        # Left side - Account list
        left_frame = ctk.CTkFrame(dashboard_split)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=0)
        
        # Right side - Account details
        self.detail_frame = ctk.CTkFrame(dashboard_split)
        # Details frame will be packed when an account is selected
        
        # Add title and refresh button in same row with minimal vertical space
        title_frame = ctk.CTkFrame(left_frame)
        title_frame.pack(fill="x", padx=10, pady=(2, 1))  # Minimal padding
        
        dashboard_title = ctk.CTkLabel(
            title_frame, 
            text="Account Dashboard", 
            font=ctk.CTkFont(size=18, weight="bold")  # Slightly smaller font
        )
        dashboard_title.pack(side="left", pady=0)  # No vertical padding
        
        refresh_button = ctk.CTkButton(
            title_frame,
            text="Refresh",
            command=self.refresh_dashboard,
            width=80,
            height=22  # Slightly reduced height
        )
        refresh_button.pack(side="right", padx=10, pady=0)
        
        # Compact header section that contains both Select All and column headers
        compact_header = ctk.CTkFrame(left_frame)
        compact_header.pack(fill="x", padx=10, pady=(0, 1))
        
        # Grid layout for better alignment
        compact_header.grid_columnconfigure(0, weight=0)  # For checkbox
        compact_header.grid_columnconfigure(1, weight=2)  # Name
        compact_header.grid_columnconfigure(2, weight=2)  # Email
        compact_header.grid_columnconfigure(3, weight=1)  # Created
        compact_header.grid_columnconfigure(4, weight=1)  # Status
        compact_header.grid_columnconfigure(5, weight=1)  # Actions
        
        # Select All checkbox directly in the header
        select_all_var = tk.BooleanVar(value=False)
        select_all_cb = ctk.CTkCheckBox(
            compact_header,
            text="",
            variable=select_all_var,
            command=lambda: self.toggle_select_all(select_all_var.get()),
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3,
            width=10
        )
        select_all_cb.grid(row=0, column=0, padx=5, pady=0, sticky="w")
        
        # Column headers in the same row as the checkbox
        headers = ["Name", "Email", "Created", "Status", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                compact_header, 
                text=header, 
                font=ctk.CTkFont(weight="bold", size=13),  # Slightly smaller font
                anchor="w"
            )
            label.grid(row=0, column=i+1, padx=5, pady=0, sticky="w")
        
        # Batch action buttons frame (will be shown when items are selected)
        self.batch_buttons_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.batch_buttons_frame.pack(side="top", fill="x", padx=10, pady=0)
        
        # Store checkbox variables - initialize empty dict here
        self.account_checkboxes = {}
        
        # Initially hide batch buttons - they'll be shown when selections are made
        self.update_batch_buttons()
        
        # Create scrollable frame for accounts with more vertical space now
        self.account_scroll = ctk.CTkScrollableFrame(left_frame)
        self.account_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 5))  # No top padding
        
        # Load accounts
        self.refresh_dashboard()
        
    def toggle_select_all(self, select_all):
        """Select or deselect all account checkboxes"""
        for email, var in self.account_checkboxes.items():
            var.set(select_all)
        
        # Update batch action buttons
        self.update_batch_buttons()
        
    def update_batch_buttons(self):
        """Show or hide batch action buttons based on selections"""
        # Ensure account_checkboxes exists
        if not hasattr(self, 'account_checkboxes'):
            self.account_checkboxes = {}
            return
            
        # Clear existing buttons
        for widget in self.batch_buttons_frame.winfo_children():
            widget.destroy()
            
        # Count selected accounts
        selected_count = sum(var.get() for var in self.account_checkboxes.values())
        
        if selected_count > 0:
            # Make the frame visible with compact layout
            self.batch_buttons_frame.pack(fill="x", padx=10, pady=(1, 1))
            
            # Even more compact batch buttons
            delete_button = ctk.CTkButton(
                self.batch_buttons_frame,
                text=f"Delete ({selected_count})",
                command=lambda: self.batch_delete(),
                fg_color="red",
                hover_color="darkred",
                width=100,
                height=22  # Smaller height
            )
            delete_button.pack(side="left", padx=2, pady=1)
            
            # Mark as Used button
            used_button = ctk.CTkButton(
                self.batch_buttons_frame,
                text=f"Mark Used ({selected_count})",
                command=lambda: self.batch_mark_used(True),
                fg_color="green",
                hover_color="darkgreen",
                width=100,
                height=22  # Smaller height
            )
            used_button.pack(side="left", padx=2, pady=1)
            
            # Mark as Unused button
            unused_button = ctk.CTkButton(
                self.batch_buttons_frame,
                text=f"Mark Unused ({selected_count})",
                command=lambda: self.batch_mark_used(False),
                fg_color="orange",
                hover_color="darkorange",
                width=100,
                height=22  # Smaller height
            )
            unused_button.pack(side="left", padx=2, pady=1)
        else:
            # Hide the frame when no selections
            self.batch_buttons_frame.pack_forget()
    
    def get_selected_accounts(self):
        """Get a list of selected account emails"""
        return [email for email, var in self.account_checkboxes.items() if var.get()]
        
    def batch_delete(self):
        """Delete all selected accounts"""
        selected_emails = self.get_selected_accounts()
        
        if not selected_emails:
            return
            
        # Confirm deletion
        confirm = tk.messagebox.askyesno(
            "Confirm Batch Delete", 
            f"Are you sure you want to delete {len(selected_emails)} accounts?"
        )
        
        if confirm:
            # Perform batch delete
            results = self.account_info.batch_action(selected_emails, "delete")
            
            # Update UI
            self.refresh_dashboard()
            self.refresh_visualization()
            self.close_account_details()
            
            self.show_message("Batch Delete", f"Successfully deleted {results['success']} accounts.")
    
    def batch_mark_used(self, used=True):
        """Mark all selected accounts as used or unused"""
        selected_emails = self.get_selected_accounts()
        
        if not selected_emails:
            return
            
        # Perform batch mark
        action = "mark_used" if used else "mark_unused"
        results = self.account_info.batch_action(selected_emails, action)
        
        # Update UI
        self.refresh_dashboard()
        
        status = "used" if used else "unused"
        self.show_message("Batch Update", f"Successfully marked {results['success']} accounts as {status}.")

    def refresh_dashboard(self):
        # If not authenticated, don't load private data
        if not hasattr(self, 'account_scroll') or not self.is_authenticated:
            return
            
        # Clear existing widgets in scrollable frame
        for widget in self.account_scroll.winfo_children():
            widget.destroy()
        
        # Initialize account_checkboxes if not exists
        if not hasattr(self, 'account_checkboxes'):
            self.account_checkboxes = {}
        else:
            # Reset checkbox variables
            self.account_checkboxes = {}
            
        # Get accounts
        accounts = self.account_info.get_accounts()
        
        # Add accounts to table
        for i, account in enumerate(accounts):
            # Background color based on status and used state - adjust for dark mode
            is_dark_mode = ctk.get_appearance_mode().lower() == "dark"
            
            if account.get("used", False):
                bg_color = "#0d5c63" if is_dark_mode else "#E0F2F1"  # Teal for used accounts
            elif account["status"] == "Success":
                bg_color = "#1e4d2b" if is_dark_mode else "#E8F5E9"  # Green for success
            else:
                bg_color = "#6b2b2b" if is_dark_mode else "#FFEBEE"  # Red for failed
                
            row_frame = ctk.CTkFrame(self.account_scroll)
            row_frame.pack(fill="x", padx=3, pady=(1, 0))  # Reduced padding
            row_frame.configure(fg_color=bg_color)
            
            # Add checkbox for selection
            email = account["email"]
            self.account_checkboxes[email] = tk.BooleanVar(value=False)
            
            checkbox = ctk.CTkCheckBox(
                row_frame, 
                text="",
                variable=self.account_checkboxes[email],
                command=self.update_batch_buttons,
                width=16,
                height=16,
                checkbox_width=16,
                checkbox_height=16,
                corner_radius=3,
                onvalue=True,
                offvalue=False
            )
            checkbox.grid(row=0, column=0, padx=3, pady=2)  # Reduced padding
            
            # Add data with reduced padding
            name_label = ctk.CTkLabel(row_frame, text=f"{account['first_name']} {account['last_name']}")
            if account.get("used", False):
                name_label.configure(text_color="gray")
            name_label.grid(row=0, column=1, padx=3, pady=2, sticky="w")  # Reduced padding
            
            email_label = ctk.CTkLabel(row_frame, text=account["email"])
            if account.get("used", False):
                email_label.configure(text_color="gray")
            email_label.grid(row=0, column=2, padx=3, pady=2, sticky="w")  # Reduced padding
            
            ctk.CTkLabel(row_frame, text=account["created_at"]).grid(row=0, column=3, padx=3, pady=2, sticky="w")  # Reduced padding
            
            # Status with color
            status_color = "green" if account["status"] == "Success" else "red"
            if account.get("used", False):
                status_text = "Used"
                status_color = "teal"
            else:
                status_text = account["status"]
                
            status_label = ctk.CTkLabel(row_frame, text=status_text)
            status_label.configure(text_color=status_color)
            status_label.grid(row=0, column=4, padx=3, pady=2, sticky="w")  # Reduced padding
            
            # Action buttons in more compact layout
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=5, padx=3, pady=2, sticky="e")  # Tighter padding
            
            # Grid layout for better spacing
            for j in range(6):
                row_frame.grid_columnconfigure(j, weight=[0, 2, 2, 1, 1, 1][j])
                
            # More compact action buttons
            button_height = 22
            button_width = 45
            
            # Open in browser button
            if account["status"] == "Success" and "url" in account and account["url"]:
                open_button = ctk.CTkButton(
                    actions_frame,
                    text="Open",
                    command=lambda acc=account: self.open_account(acc["url"]),
                    width=button_width,
                    height=button_height
                )
                open_button.pack(side="left", padx=1)
            
            # Copy info button
            copy_button = ctk.CTkButton(
                actions_frame,
                text="Copy",
                command=lambda acc=account: self.copy_account_info(acc),
                width=button_width,
                height=button_height
            )
            copy_button.pack(side="left", padx=1)
            
            # Mark as used/unused button
            if account.get("used", False):
                used_button = ctk.CTkButton(
                    actions_frame,
                    text="Unused",
                    command=lambda acc=account: self.mark_account_used(acc, False),
                    width=button_width,
                    height=button_height,
                    fg_color="orange",
                    hover_color="darkorange"
                )
                used_button.pack(side="left", padx=1)
            else:
                used_button = ctk.CTkButton(
                    actions_frame,
                    text="Used",
                    command=lambda acc=account: self.mark_account_used(acc, True),
                    width=button_width,
                    height=button_height,
                    fg_color="teal",
                    hover_color="darkslategray"
                )
                used_button.pack(side="left", padx=1)
            
            # Configure grid
            for j in range(6):
                row_frame.grid_columnconfigure(j, weight=[0, 2, 2, 1, 1, 1][j])
                
            # Add hover effect
            def on_enter(e, rf=row_frame):
                is_dark = ctk.get_appearance_mode().lower() == "dark"
                original_color = rf.cget("fg_color")
                
                if account.get("used", False):
                    rf.configure(fg_color="#107a82" if is_dark else "#B2DFDB")  # Darker teal
                elif account["status"] == "Success":
                    rf.configure(fg_color="#2a6b3c" if is_dark else "#C8E6C9")  # Darker green
                else:
                    rf.configure(fg_color="#8c3a3a" if is_dark else "#FFCDD2")  # Darker red
            
            def on_leave(e, rf=row_frame):
                is_dark = ctk.get_appearance_mode().lower() == "dark"
                
                if account.get("used", False):
                    rf.configure(fg_color="#0d5c63" if is_dark else "#E0F2F1")  # Teal
                elif account["status"] == "Success":
                    rf.configure(fg_color="#1e4d2b" if is_dark else "#E8F5E9")  # Green
                else:
                    rf.configure(fg_color="#6b2b2b" if is_dark else "#FFEBEE")  # Red
            
            # Make the row clickable to show details
            def show_detail(e, acc=account):
                self.show_account_details(acc)
                
            row_frame.bind("<Enter>", on_enter)
            row_frame.bind("<Leave>", on_leave)
            row_frame.bind("<Button-1>", show_detail)
            
            # Make child labels clickable too (except checkbox)
            for child in row_frame.winfo_children()[1:]:  # Skip checkbox
                child.bind("<Button-1>", lambda e, acc=account: self.show_account_details(acc))
        
        # Check if we need to show batch action buttons
        self.update_batch_buttons()
            
    def mark_account_used(self, account, used=True):
        """Mark an account as used or unused"""
        if self.account_info.mark_account_used(account["email"], used):
            self.refresh_dashboard()
            
            status = "used" if used else "unused"
            self.show_message(
                "Account Updated", 
                f"Account {account['email']} marked as {status}."
            )
            
            # If current account details are displayed, refresh them
            if self.account_detail and self.account_detail["email"] == account["email"]:
                # Get updated account data
                for acc in self.account_info.get_accounts():
                    if acc["email"] == account["email"]:
                        self.show_account_details(acc)
                        break
    
    def show_account_details(self, account):
        # If detail frame is not packed, add it
        if not self.detail_frame.winfo_children():
            self.detail_frame.pack(side="right", fill="both", expand=False, padx=(5, 0), pady=0, ipadx=10, ipady=10, anchor="n")
            self.detail_frame.configure(width=300)
        else:
            # Clear existing widgets
            for widget in self.detail_frame.winfo_children():
                widget.destroy()
                
        # Update the currently selected account
        self.account_detail = account
        
        # Create detail view
        detail_title = ctk.CTkLabel(
            self.detail_frame, 
            text="Account Details", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        detail_title.pack(pady=10)
        
        # Add close button for detail view
        close_button = ctk.CTkButton(
            self.detail_frame,
            text="Close Details",
            command=self.close_account_details,
            width=100,
            fg_color="gray",
            hover_color="darkgray"
        )
        close_button.pack(pady=(0, 20))
        
        # Create fields
        fields_frame = ctk.CTkFrame(self.detail_frame)
        fields_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status indicator at the top
        status_color = "green" if account["status"] == "Success" else "red"
        if account.get("used", False):
            status_color = "teal"
            
        status_frame = ctk.CTkFrame(fields_frame, fg_color=status_color)
        status_frame.pack(fill="x", padx=10, pady=10)
        
        status_text = account["status"]
        if account.get("used", False):
            status_text = f"Used - {account['status']}"
            
        status_label = ctk.CTkLabel(
            status_frame, 
            text=f"Status: {status_text}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        status_label.pack(pady=10)
        
        # Last used date if available
        if account.get("used", False) and account.get("last_used"):
            last_used = ctk.CTkLabel(
                status_frame,
                text=f"Last Used: {account['last_used']}",
                font=ctk.CTkFont(size=12),
                text_color="white"
            )
            last_used.pack(pady=(0, 10))
        
        # Account info
        self.add_detail_field(fields_frame, "First Name", account["first_name"])
        self.add_detail_field(fields_frame, "Last Name", account["last_name"])
        self.add_detail_field(fields_frame, "Email", account["email"])
        self.add_detail_field(fields_frame, "Password", account["password"], True)
        self.add_detail_field(fields_frame, "Created", account["created_at"])
        if "url" in account and account["url"]:
            self.add_detail_field(fields_frame, "URL", account["url"], is_url=True)
        
        # Add action buttons
        action_frame = ctk.CTkFrame(fields_frame)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        # Add Open Account button if URL exists and is valid
        has_valid_url = "url" in account and account["url"] and account["url"] not in ["Unknown", ""]
        if has_valid_url and account["status"] == "Success":
            open_button = ctk.CTkButton(
                action_frame,
                text="Open Account",
                command=lambda: self.open_account(account["url"]),
                fg_color="blue",
                hover_color="darkblue"
            )
            open_button.pack(fill="x", pady=5)
        
        copy_button = ctk.CTkButton(
            action_frame,
            text="Copy Account Info",
            command=lambda: self.copy_account_info(account)
        )
        copy_button.pack(fill="x", pady=5)
        
        # Toggle used status button
        if account.get("used", False):
            mark_button = ctk.CTkButton(
                action_frame,
                text="Mark as Unused",
                command=lambda: self.mark_account_used(account, False),
                fg_color="orange",
                hover_color="darkorange"
            )
        else:
            mark_button = ctk.CTkButton(
                action_frame,
                text="Mark as Used",
                command=lambda: self.mark_account_used(account, True),
                fg_color="teal",
                hover_color="darkslategray"
            )
        mark_button.pack(fill="x", pady=5)
        
        delete_button = ctk.CTkButton(
            action_frame,
            text="Delete Account",
            command=lambda: self.delete_account(account),
            fg_color="red",
            hover_color="darkred"
        )
        delete_button.pack(fill="x", pady=5)
    
    def add_detail_field(self, parent, label_text, value, is_password=False, is_url=False):
        """Add a field to the detail view"""
        field_frame = ctk.CTkFrame(parent)
        field_frame.pack(fill="x", padx=10, pady=5)
        
        label = ctk.CTkLabel(
            field_frame, 
            text=f"{label_text}:",
            font=ctk.CTkFont(weight="bold"),
            width=100,
            anchor="w"
        )
        label.pack(side="left", padx=5, pady=5)
        
        # Password handling with show/hide functionality
        if is_password:
            # Create a container for the password field and buttons
            password_container = ctk.CTkFrame(field_frame, fg_color="transparent")
            password_container.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            
            # Create a StringVar to store the displayed password value
            password_var = tk.StringVar(value="••••••••")
            password_shown = False
            
            # Password value label
            value_label = ctk.CTkLabel(
                password_container, 
                textvariable=password_var,
                anchor="w"
            )
            value_label.pack(side="left", fill="x", expand=True)
            
            # Function to toggle password visibility
            def toggle_password():
                nonlocal password_shown
                password_shown = not password_shown
                if password_shown:
                    password_var.set(value)
                    show_btn.configure(text="👁️", hover_color="#e5e5e5", fg_color="#d1d1d1")
                else:
                    password_var.set("••••••••")
                    show_btn.configure(text="👁️", hover_color="#e5e5e5", fg_color="transparent")
            
            # Show password button
            show_btn = ctk.CTkButton(
                field_frame,
                text="👁️",
                width=30,
                height=25,
                command=toggle_password,
                fg_color="transparent",
                hover_color="#e5e5e5"
            )
            show_btn.pack(side="right", padx=(0, 5), pady=5)
            
            # Copy button
            copy_button = ctk.CTkButton(
                field_frame,
                text="📋",
                width=30,
                height=25,
                command=lambda: self.copy_to_clipboard(value, "Password copied to clipboard"),
                fg_color="transparent",
                hover_color="#e5e5e5"
            )
            copy_button.pack(side="right", padx=5, pady=5)
            
        elif is_url:
            # Truncate URL for display
            display_value = value
            if len(value) > 25:
                display_value = value[:22] + "..."
                
            # URL value label
            value_label = ctk.CTkLabel(
                field_frame, 
                text=display_value,
                anchor="w"
            )
            value_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)
            
            # Add open button for URL
            open_button = ctk.CTkButton(
                field_frame,
                text="🔗",
                width=30,
                height=25,
                command=lambda: self.open_account(value),
                fg_color="transparent",
                hover_color="#e5e5e5"
            )
            open_button.pack(side="right", padx=5, pady=5)
            
            # Add copy button for URL
            copy_button = ctk.CTkButton(
                field_frame,
                text="📋",
                width=30,
                height=25,
                command=lambda: self.copy_to_clipboard(value, "URL copied to clipboard"),
                fg_color="transparent",
                hover_color="#e5e5e5"
            )
            copy_button.pack(side="right", padx=5, pady=5)
        else:
            # Regular value field
            value_label = ctk.CTkLabel(
                field_frame, 
                text=value,
                anchor="w"
            )
            value_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)
            
            # Add copy button for regular fields
            copy_button = ctk.CTkButton(
                field_frame,
                text="📋",
                width=30,
                height=25,
                command=lambda: self.copy_to_clipboard(value, f"{label_text} copied to clipboard"),
                fg_color="transparent",
                hover_color="#e5e5e5"
            )
            copy_button.pack(side="right", padx=5, pady=5)
    
    def close_account_details(self):
        """Close the account details panel"""
        # Remove all widgets
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
            
        # Hide the frame
        self.detail_frame.pack_forget()
        
        # Clear the selected account
        self.account_detail = None
    
    def open_account(self, url):
        """Open the account URL in the default browser"""
        import webbrowser
        webbrowser.open(url)
    
    def copy_account_info(self, account):
        """Copy account information to clipboard"""
        # Format account info
        info = f"Email: {account['email']}\nPassword: {account['password']}"
        
        # Copy to clipboard
        self.copy_to_clipboard(info, "Account info copied to clipboard")
    
    def copy_to_clipboard(self, text, message=None):
        """Copy text to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(text)
        
        if message:
            self.show_message("Copied", message)
    
    def delete_account(self, account):
        """Delete an account"""
        # Confirm deletion
        confirm = tk.messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete the account {account['email']}?"
        )
        
        if confirm:
            # Get current accounts
            accounts = self.account_info.get_accounts()
            
            # Find and remove account
            for i, acc in enumerate(accounts):
                if acc["email"] == account["email"]:
                    # Remove from list
                    del self.account_info.accounts["accounts"][i]
                    
                    # Update statistics
                    if acc["status"] == "Success":
                        self.account_info.accounts["statistics"]["success"] -= 1
                    else:
                        self.account_info.accounts["statistics"]["failed"] -= 1
                    
                    # Save changes
                    self.account_info.save_accounts()
                    
                    # Close detail view
                    self.close_account_details()
                    
                    # Refresh UI
                    self.refresh_dashboard()
                    self.refresh_visualization()
                    
                    # Show confirmation
                    self.show_message("Account Deleted", f"Account {account['email']} has been deleted.")
                    return
    
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
            
            # Create shell link
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
            shortcut.Arguments = os.path.abspath(__file__)
            shortcut.IconLocation = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            
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

    def setup_settings_tab(self):
        # Create scrollable frame for settings
        self.settings_scroll = ctk.CTkScrollableFrame(self.tab_settings)
        self.settings_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Create settings frame
        self.settings_frame = ctk.CTkFrame(self.settings_scroll)
        self.settings_frame.pack(fill="x", padx=10, pady=10)
        
        # Add title
        settings_title = ctk.CTkLabel(
            self.settings_frame, 
            text="Settings", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        settings_title.pack(pady=10)
        
        # APPEARANCE SETTINGS
        appearance_frame = ctk.CTkFrame(self.settings_frame)
        appearance_frame.pack(fill="x", padx=10, pady=10)
        
        appearance_label = ctk.CTkLabel(
            appearance_frame, 
            text="Appearance", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        appearance_label.pack(anchor="w", padx=10, pady=5)
        
        # Appearance mode
        appearance_mode_frame = ctk.CTkFrame(appearance_frame)
        appearance_mode_frame.pack(fill="x", padx=10, pady=5)
        
        appearance_mode_label = ctk.CTkLabel(appearance_mode_frame, text="Theme:", width=150)
        appearance_mode_label.pack(side="left", padx=10, pady=5)
        
        appearance_mode_menu = ctk.CTkOptionMenu(
            appearance_mode_frame, 
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode
        )
        appearance_mode_menu.set("System")
        appearance_mode_menu.pack(side="left", padx=10, pady=5)
        
        # UI scaling
        scaling_frame = ctk.CTkFrame(appearance_frame)
        scaling_frame.pack(fill="x", padx=10, pady=5)
        
        scaling_label = ctk.CTkLabel(scaling_frame, text="UI Scaling:", width=150)
        scaling_label.pack(side="left", padx=10, pady=5)
        
        scaling_menu = ctk.CTkOptionMenu(
            scaling_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event
        )
        scaling_menu.set("100%")
        scaling_menu.pack(side="left", padx=10, pady=5)
        
        # DASHBOARD LOGIN SETTINGS
        login_frame = ctk.CTkFrame(self.settings_frame)
        login_frame.pack(fill="x", padx=10, pady=10)
        
        login_label = ctk.CTkLabel(
            login_frame, 
            text="Dashboard Login", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        login_label.pack(anchor="w", padx=10, pady=5)
        
        # Dashboard login toggle
        login_toggle_frame = ctk.CTkFrame(login_frame)
        login_toggle_frame.pack(fill="x", padx=10, pady=5)
        
        login_toggle_label = ctk.CTkLabel(login_toggle_frame, text="Require Authentication:", width=150)
        login_toggle_label.pack(side="left", padx=10, pady=5)
        
        self.dashboard_login_var = tk.BooleanVar(value=True)
        login_toggle_switch = ctk.CTkSwitch(
            login_toggle_frame,
            text="",
            variable=self.dashboard_login_var,
            command=self.toggle_dashboard_login
        )
        login_toggle_switch.pack(side="left", padx=10, pady=5)
        
        # BACKUP & SYNC SETTINGS
        backup_frame = ctk.CTkFrame(self.settings_frame)
        backup_frame.pack(fill="x", padx=10, pady=10)
        
        backup_label = ctk.CTkLabel(
            backup_frame, 
            text="Backup & Sync", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        backup_label.pack(anchor="w", padx=10, pady=5)
        
        # Create backup button
        backup_button_frame = ctk.CTkFrame(backup_frame)
        backup_button_frame.pack(fill="x", padx=10, pady=5)
        
        create_backup_button = ctk.CTkButton(
            backup_button_frame,
            text="Create Backup Now",
            command=self.create_manual_backup
        )
        create_backup_button.pack(side="left", padx=10, pady=5)
        
        # Restore from backup button
        restore_backup_button = ctk.CTkButton(
            backup_button_frame,
            text="Restore From Backup",
            command=self.show_restore_dialog,
            fg_color="orange",
            hover_color="darkorange"
        )
        restore_backup_button.pack(side="left", padx=10, pady=5)
        
        # DESKTOP SHORTCUT
        shortcut_frame = ctk.CTkFrame(self.settings_frame)
        shortcut_frame.pack(fill="x", padx=10, pady=10)
        
        shortcut_label = ctk.CTkLabel(
            shortcut_frame, 
            text="Desktop Integration", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        shortcut_label.pack(anchor="w", padx=10, pady=5)
        
        # Create desktop shortcut button
        shortcut_button_frame = ctk.CTkFrame(shortcut_frame)
        shortcut_button_frame.pack(fill="x", padx=10, pady=5)
        
        create_shortcut_button = ctk.CTkButton(
            shortcut_button_frame,
            text="Create Desktop Shortcut",
            command=self.create_desktop_shortcut
        )
        create_shortcut_button.pack(side="left", padx=10, pady=5)
        
        # SECURITY SETTINGS
        security_frame = ctk.CTkFrame(self.settings_frame)
        security_frame.pack(fill="x", padx=10, pady=10)
        
        security_label = ctk.CTkLabel(
            security_frame, 
            text="Security", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        security_label.pack(anchor="w", padx=10, pady=5)
        
        # Change password
        pwd_frame = ctk.CTkFrame(security_frame)
        pwd_frame.pack(fill="x", padx=10, pady=5)
        
        current_pwd_label = ctk.CTkLabel(pwd_frame, text="Current Password:", width=150)
        current_pwd_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.current_pwd = tk.StringVar()
        current_pwd_entry = ctk.CTkEntry(pwd_frame, textvariable=self.current_pwd, show="•", width=200, height=30)
        current_pwd_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        new_pwd_label = ctk.CTkLabel(pwd_frame, text="New Password:", width=150)
        new_pwd_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.new_pwd = tk.StringVar()
        new_pwd_entry = ctk.CTkEntry(pwd_frame, textvariable=self.new_pwd, show="•", width=200, height=30)
        new_pwd_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        confirm_pwd_label = ctk.CTkLabel(pwd_frame, text="Confirm Password:", width=150)
        confirm_pwd_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.confirm_pwd = tk.StringVar()
        confirm_pwd_entry = ctk.CTkEntry(pwd_frame, textvariable=self.confirm_pwd, show="•", width=200, height=30)
        confirm_pwd_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        change_pwd_button = ctk.CTkButton(
            pwd_frame, 
            text="Update Password",
            command=self.change_password,
            fg_color="#3a7ebf",
            hover_color="#2a6eaf"
        )
        change_pwd_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)
        
        # DATA MANAGEMENT
        data_frame = ctk.CTkFrame(self.settings_frame)
        data_frame.pack(fill="x", padx=10, pady=10)
        
        data_label = ctk.CTkLabel(
            data_frame, 
            text="Data Management", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        data_label.pack(anchor="w", padx=10, pady=5)
        
        # Data options
        data_buttons_frame = ctk.CTkFrame(data_frame)
        data_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        export_button = ctk.CTkButton(
            data_buttons_frame,
            text="Export Data",
            command=self.export_data
        )
        export_button.pack(side="left", padx=10, pady=5)
        
        import_button = ctk.CTkButton(
            data_buttons_frame,
            text="Import JSON",
            command=self.import_json_data,
            fg_color="#3a7ebf",
            hover_color="#2a6eaf"
        )
        import_button.pack(side="left", padx=10, pady=5)
        
        clear_button = ctk.CTkButton(
            data_buttons_frame,
            text="Clear All Data",
            command=self.clear_data,
            fg_color="red",
            hover_color="darkred"
        )
        clear_button.pack(side="left", padx=10, pady=5)

    def import_json_data(self):
        """Import account data from a JSON file"""
        from tkinter import filedialog
        
        # Show file dialog
        file_path = filedialog.askopenfilename(
            title="Import Account Data",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return  # User canceled
            
        try:
            # Read JSON file
            with open(file_path, "r") as f:
                import_data = json.load(f)
                
            # Validate data structure
            if not isinstance(import_data, dict) or "accounts" not in import_data:
                self.show_message("Import Error", "Invalid data format. File must contain an 'accounts' key.")
                return
                
            # Ask if user wants to merge or replace
            confirm = tk.messagebox.askyesno(
                "Import Options", 
                "Do you want to MERGE with existing data?\n\n"
                "Yes = Merge (add imported accounts to existing)\n"
                "No = Replace (overwrite all existing data)"
            )
            
            if confirm:  # Merge
                # Get existing accounts
                existing_accounts = self.account_info.get_accounts()
                existing_emails = [acc["email"] for acc in existing_accounts]
                
                # Add imported accounts that don't already exist
                added = 0
                for account in import_data["accounts"]:
                    if "email" in account and account["email"] not in existing_emails:
                        self.account_info.accounts["accounts"].append(account)
                        
                        # Update statistics based on status
                        if account.get("status") == "Success":
                            self.account_info.accounts["statistics"]["success"] += 1
                        else:
                            self.account_info.accounts["statistics"]["failed"] += 1
                            
                        added += 1
                        existing_emails.append(account["email"])
                        
                # Save changes
                self.account_info.save_accounts()
                
                # Display result
                self.show_message("Import Complete", f"Successfully added {added} new accounts.")
                
            else:  # Replace
                # Create backup of current data before replacing
                backup_path = self.account_info.create_backup()
                
                # Replace all data
                self.account_info.accounts = import_data
                
                # Make sure statistics are correct
                if "statistics" not in self.account_info.accounts:
                    success_count = len([a for a in import_data["accounts"] if a.get("status") == "Success"])
                    failed_count = len([a for a in import_data["accounts"] if a.get("status") != "Success"])
                    
                    self.account_info.accounts["statistics"] = {
                        "success": success_count,
                        "failed": failed_count
                    }
                    
                # Make sure settings exists
                if "settings" not in self.account_info.accounts:
                    self.account_info.accounts["settings"] = {"auth_password": "turbolearn123"}
                    
                # Save changes
                self.account_info.save_accounts()
                
                # Display result
                self.show_message(
                    "Import Complete", 
                    f"Successfully replaced data with {len(import_data['accounts'])} accounts.\n"
                    f"A backup of your previous data was created at: {backup_path}"
                )
            
            # Ensure authentication state is set for dashboard access
            if not self.is_authenticated:
                if hasattr(self, 'dashboard_login_var') and not self.dashboard_login_var.get():
                    self.is_authenticated = True
                    # Recreate dashboard content if on dashboard tab
                    if self.tabview.get() == "Dashboard":
                        for widget in self.dashboard_frame.winfo_children():
                            widget.destroy()
                        self.create_dashboard_content()
                else:
                    # Show authentication screen
                    for widget in self.dashboard_frame.winfo_children():
                        widget.destroy()
                    self.create_auth_panel()
                
            # Refresh UI
            self.force_refresh_dashboard()
            self.refresh_visualization()
                
        except Exception as e:
            self.show_message("Import Error", f"Failed to import data: {str(e)}")
            import traceback
            traceback.print_exc()

    def setup_visualization_tab(self):
        """Setup the visualization tab with charts and analytics"""
        # Create frame for visualizations
        viz_frame = ctk.CTkFrame(self.tab_visualization)
        viz_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add title
        viz_title = ctk.CTkLabel(
            viz_frame, 
            text="Account Analytics", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        viz_title.pack(pady=10)
        
        # Create frame for charts
        charts_frame = ctk.CTkFrame(viz_frame)
        charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create left and right frames for charts
        left_chart = ctk.CTkFrame(charts_frame)
        left_chart.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        right_chart = ctk.CTkFrame(charts_frame)
        right_chart.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Placeholder message if no data
        left_placeholder = ctk.CTkLabel(
            left_chart, 
            text="Success rate chart will appear here\nwhen you create accounts.",
            font=ctk.CTkFont(size=14)
        )
        left_placeholder.pack(pady=50)
        
        right_placeholder = ctk.CTkLabel(
            right_chart, 
            text="Account timeline will appear here\nwhen you create accounts.",
            font=ctk.CTkFont(size=14)
        )
        right_placeholder.pack(pady=50)
        
        # Add refresh button
        refresh_button = ctk.CTkButton(
            viz_frame,
            text="Refresh Charts",
            command=self.refresh_visualization
        )
        refresh_button.pack(pady=10)
        
        # Store chart frames for later use
        self.viz_frame = viz_frame
        self.charts_frame = charts_frame
    
    def refresh_visualization(self):
        """Refresh visualization charts with latest data"""
        # Clear existing widgets in charts frame
        for widget in self.charts_frame.winfo_children():
            widget.destroy()
            
        # Get statistics
        stats = self.account_info.get_statistics()
        accounts = self.account_info.get_accounts()
        
        # Create left and right frames for charts
        left_chart = ctk.CTkFrame(self.charts_frame)
        left_chart.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        right_chart = ctk.CTkFrame(self.charts_frame)
        right_chart.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Create figure for left chart - Success vs Failed
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            fig1 = plt.Figure(figsize=(5, 4), dpi=100)
            ax1 = fig1.add_subplot(111)
            
            # Data for pie chart
            labels = ['Success', 'Failed']
            sizes = [stats["success"], stats["failed"]]
            colors = ['#4CAF50', '#F44336']
            
            # Create pie chart
            if sum(sizes) > 0:  # Only create chart if we have data
                ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                ax1.set_title('Success Rate')
                
                # Create canvas for pie chart
                canvas1 = FigureCanvasTkAgg(fig1, left_chart)
                canvas1.draw()
                canvas1.get_tk_widget().pack(fill="both", expand=True)
            else:
                # No data message
                no_data = ctk.CTkLabel(
                    left_chart, 
                    text="No data available yet.\nCreate accounts to see statistics.",
                    font=ctk.CTkFont(size=14)
                )
                no_data.pack(pady=50)
            
            # Create figure for right chart - Timeline of account creation
            if len(accounts) > 0:
                fig2 = plt.Figure(figsize=(5, 4), dpi=100)
                ax2 = fig2.add_subplot(111)
                
                # Extract dates and statuses
                dates = []
                statuses = []
                for acc in accounts:
                    try:
                        date = datetime.strptime(acc["created_at"], "%Y-%m-%d %H:%M:%S")
                        status = 1 if acc["status"] == "Success" else 0
                        dates.append(date)
                        statuses.append(status)
                    except:
                        pass
                        
                # Sort by date
                date_status = sorted(zip(dates, statuses), key=lambda x: x[0])
                if date_status:
                    dates, statuses = zip(*date_status)
                    
                    # Create cumulative sum line
                    cumulative = [sum(statuses[:i+1]) for i in range(len(statuses))]
                    
                    # Plot
                    ax2.plot(dates, cumulative, marker='o', linestyle='-', color='blue')
                    ax2.set_title('Accounts Created Over Time')
                    ax2.set_xlabel('Date')
                    ax2.set_ylabel('Total Successful Accounts')
                    
                    # Format dates properly
                    fig2.autofmt_xdate()
                    
                    # Create canvas for line chart
                    canvas2 = FigureCanvasTkAgg(fig2, right_chart)
                    canvas2.draw()
                    canvas2.get_tk_widget().pack(fill="both", expand=True)
                else:
                    # No valid date data
                    no_data = ctk.CTkLabel(
                        right_chart, 
                        text="No valid date data available.",
                        font=ctk.CTkFont(size=14)
                    )
                    no_data.pack(pady=50)
            else:
                # No data message
                no_data = ctk.CTkLabel(
                    right_chart, 
                    text="No data available yet.\nCreate accounts to see timeline.",
                    font=ctk.CTkFont(size=14)
                )
                no_data.pack(pady=50)
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_label = ctk.CTkLabel(
                left_chart,
                text=f"Error creating charts: {str(e)}\nMake sure matplotlib is installed.",
                font=ctk.CTkFont(size=14),
                text_color="red"
            )
            error_label.pack(pady=20)

    def show_restore_dialog(self):
        """Show dialog to restore from a backup"""
        # Get available backups
        backups = self.account_info.get_available_backups()
        
        if not backups:
            self.show_message("No Backups", "No backup files were found.")
            return
            
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Restore from Backup")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Add title
        title = ctk.CTkLabel(
            dialog, 
            text="Select a Backup to Restore", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=10)
        
        # Add list of backups
        backup_frame = ctk.CTkScrollableFrame(dialog)
        backup_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        selected_backup = tk.StringVar()
        
        for i, backup in enumerate(backups):
            backup_row = ctk.CTkFrame(backup_frame)
            backup_row.pack(fill="x", padx=5, pady=2)
            
            radio = ctk.CTkRadioButton(
                backup_row,
                text="",
                variable=selected_backup,
                value=backup["path"]
            )
            radio.pack(side="left", padx=5, pady=5)
            
            info_frame = ctk.CTkFrame(backup_row)
            info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            
            date_label = ctk.CTkLabel(
                info_frame,
                text=f"Date: {backup['timestamp']}",
                font=ctk.CTkFont(weight="bold")
            )
            date_label.pack(anchor="w")
            
            size_label = ctk.CTkLabel(
                info_frame,
                text=f"Size: {backup['size']}"
            )
            size_label.pack(anchor="w")
            
            # Select first backup by default
            if i == 0:
                selected_backup.set(backup["path"])
                
        # Add buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def restore_selected():
            backup_path = selected_backup.get()
            dialog.destroy()
            
            if backup_path:
                confirm = tk.messagebox.askyesno(
                    "Confirm Restore", 
                    "Are you sure you want to restore this backup? All current data will be replaced."
                )
                
                if confirm:
                    if self.account_info.restore_from_backup(backup_path):
                        self.show_message("Restore Complete", "Data has been restored from the backup.")
                        self.refresh_dashboard()
                        self.refresh_visualization()
                    else:
                        self.show_message("Restore Failed", "Failed to restore from backup.")
        
        restore_button = ctk.CTkButton(
            button_frame,
            text="Restore Selected Backup",
            command=restore_selected,
            fg_color="orange",
            hover_color="darkorange"
        )
        restore_button.pack(side="left", padx=10, pady=10)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_button.pack(side="right", padx=10, pady=10)

    def create_manual_backup(self):
        """Create a manual backup of account data"""
        backup_path = self.account_info.create_backup()
        if backup_path:
            self.show_message("Backup Created", f"Backup saved to: {backup_path}")
        else:
            self.show_message("Backup Failed", "Could not create backup. See console for details.")

    def force_refresh_dashboard(self):
        """Force refresh the dashboard without authentication check"""
        # Temporarily set authentication to true
        original_auth_state = self.is_authenticated
        self.is_authenticated = True
        
        # If on dashboard tab and not set up correctly, initialize it
        if self.tabview.get() == "Dashboard" and not hasattr(self, 'account_scroll'):
            # Clear dashboard frame
            for widget in self.dashboard_frame.winfo_children():
                widget.destroy()
            # Create dashboard content
            self.create_dashboard_content()
        
        # Refresh the dashboard display
        self.refresh_dashboard()
        
        # Restore original authentication state
        self.is_authenticated = original_auth_state
    
    def check_current_tab(self):
        """Check which tab is currently selected and handle the change"""
        current_tab = self.tabview.get()
        
        # Call our tab change handler with the current tab
        self.on_tab_change(current_tab)
        
        # Schedule the next check (every 300ms)
        self.after(300, self.check_current_tab)

    def setup_home_tab(self):
        """Setup the Home tab with student utilities: schedule, weather, and system tools"""
        # Main container with scrollable frame
        self.home_scroll = ctk.CTkScrollableFrame(self.tab_home)
        self.home_scroll.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Create top row with welcome message and date/time
        top_frame = ctk.CTkFrame(self.home_scroll, height=60)  # Fixed height
        top_frame.pack(fill="x", padx=10, pady=(5, 5))  # Reduced padding
        
        # Welcome message
        self.welcome_label = ctk.CTkLabel(
            top_frame,
            text="Welcome to TurboLearn Student Dashboard",
            font=ctk.CTkFont(size=18, weight="bold")  # Smaller font
        )
        self.welcome_label.pack(side="left", padx=10, pady=5)  # Reduced padding
        
        # Date and time display
        self.datetime_label = ctk.CTkLabel(
            top_frame,
            text="",
            font=ctk.CTkFont(size=12)  # Smaller font
        )
        self.datetime_label.pack(side="right", padx=10, pady=5)  # Reduced padding
        
        # Update time function
        def update_time():
            current_time = datetime.now().strftime("%A, %B %d, %Y  %H:%M:%S")
            self.datetime_label.configure(text=current_time)
            self.after(1000, update_time)  # Update every second
        
        # Start time update
        update_time()
        
        # SCHEDULE SECTION - Main focal point
        schedule_frame = ctk.CTkFrame(self.home_scroll)
        schedule_frame.pack(fill="x", expand=True, padx=10, pady=(5, 5))  # Reduced padding
        
        # Schedule title frame with bright background
        schedule_title_frame = ctk.CTkFrame(schedule_frame, fg_color="#c8ff00", height=40)  # Fixed height
        schedule_title_frame.pack(fill="x", padx=0, pady=(0, 5))  # Reduced padding
        
        schedule_title = ctk.CTkLabel(
            schedule_title_frame,
            text="schedule",
            font=ctk.CTkFont(size=22, weight="bold"),  # Smaller font
            text_color="#6242f5",  # Purple text color
            fg_color="transparent"
        )
        schedule_title.pack(pady=8)  # Reduced padding
        
        # Create the main schedule container
        self.schedule_container = ctk.CTkFrame(schedule_frame)
        self.schedule_container.pack(fill="both", expand=True, padx=5, pady=2)  # Reduced padding
        
        # Display schedule in grid format
        self.create_schedule_grid()
        
        # Add edit button for schedule
        edit_schedule_btn = ctk.CTkButton(
            schedule_frame,
            text="Edit Schedule",
            command=self.edit_schedule,
            height=28  # Reduced height
        )
        edit_schedule_btn.pack(padx=10, pady=(2, 5))  # Reduced padding
        
        # Create container for weather and utilities (will appear when scrolling down)
        features_frame = ctk.CTkFrame(self.home_scroll)
        features_frame.pack(fill="x", expand=True, padx=10, pady=(0, 5))  # Reduced padding
        
        # Create middle frame for weather
        weather_frame = ctk.CTkFrame(features_frame)
        weather_frame.pack(side="left", fill="both", expand=True, padx=2, pady=2)  # Reduced padding
        
        weather_title = ctk.CTkLabel(
            weather_frame,
            text="🌤️ Weather Updates",
            font=ctk.CTkFont(size=14, weight="bold")  # Smaller font
        )
        weather_title.pack(anchor="nw", padx=8, pady=5)  # Reduced padding
        
        # Weather content
        self.weather_content = ctk.CTkFrame(weather_frame)
        self.weather_content.pack(fill="both", expand=True, padx=5, pady=5)  # Reduced padding
        
        # Location entry and button
        location_frame = ctk.CTkFrame(self.weather_content)
        location_frame.pack(fill="x", padx=5, pady=2)  # Reduced padding
        
        self.location_var = tk.StringVar(value="New York")
        location_entry = ctk.CTkEntry(
            location_frame,
            placeholder_text="Enter city",
            textvariable=self.location_var,
            width=120,  # Reduced width
            height=28  # Reduced height
        )
        location_entry.pack(side="left", padx=2, pady=2)  # Reduced padding
        
        get_weather_btn = ctk.CTkButton(
            location_frame,
            text="Get Weather",
            command=self.fetch_weather,
            height=28,  # Reduced height
            width=100  # Reduced width
        )
        get_weather_btn.pack(side="left", padx=2, pady=2)  # Reduced padding
        
        # Weather display
        self.weather_display = ctk.CTkFrame(self.weather_content)
        self.weather_display.pack(fill="both", expand=True, padx=5, pady=2)  # Reduced padding
        
        self.weather_icon_label = ctk.CTkLabel(
            self.weather_display,
            text="☀️",  # Default icon
            font=ctk.CTkFont(size=36)  # Smaller font
        )
        self.weather_icon_label.pack(pady=5)  # Reduced padding
        
        self.temperature_label = ctk.CTkLabel(
            self.weather_display,
            text="-- °C",
            font=ctk.CTkFont(size=18, weight="bold")  # Smaller font
        )
        self.temperature_label.pack(pady=2)  # Reduced padding
        
        self.condition_label = ctk.CTkLabel(
            self.weather_display,
            text="--",
            font=ctk.CTkFont(size=14)  # Smaller font
        )
        self.condition_label.pack(pady=2)  # Reduced padding
        
        self.details_frame = ctk.CTkFrame(self.weather_display)
        self.details_frame.pack(fill="x", padx=5, pady=2)  # Reduced padding
        
        self.humidity_label = ctk.CTkLabel(
            self.details_frame,
            text="Humidity: --%",
            font=ctk.CTkFont(size=12),  # Smaller font
            anchor="w"
        )
        self.humidity_label.pack(fill="x", pady=1)  # Reduced padding
        
        self.wind_label = ctk.CTkLabel(
            self.details_frame,
            text="Wind: -- km/h",
            font=ctk.CTkFont(size=12),  # Smaller font
            anchor="w"
        )
        self.wind_label.pack(fill="x", pady=1)  # Reduced padding
        
        self.last_updated_label = ctk.CTkLabel(
            self.weather_display,
            text="Last updated: --",
            font=ctk.CTkFont(size=10),  # Smaller font
            text_color="gray"
        )
        self.last_updated_label.pack(pady=2)  # Reduced padding
        
        # Create right frame for utilities
        utilities_frame = ctk.CTkFrame(features_frame)
        utilities_frame.pack(side="left", fill="both", expand=True, padx=2, pady=2)  # Reduced padding
        
        utilities_title = ctk.CTkLabel(
            utilities_frame,
            text="🛠️ Utility Tools",
            font=ctk.CTkFont(size=14, weight="bold")  # Smaller font
        )
        utilities_title.pack(anchor="nw", padx=8, pady=5)  # Reduced padding
        
        # System utilities scrollable frame
        utilities_scroll = ctk.CTkScrollableFrame(utilities_frame, height=200)  # Fixed height
        utilities_scroll.pack(fill="both", expand=True, padx=5, pady=2)  # Reduced padding
        
        # Restart Explorer
        explorer_frame = ctk.CTkFrame(utilities_scroll)
        explorer_frame.pack(fill="x", padx=2, pady=2)  # Reduced padding
        
        explorer_label = ctk.CTkLabel(
            explorer_frame,
            text="Restart Windows Explorer",
            font=ctk.CTkFont(size=12, weight="bold"),  # Smaller font
            anchor="w"
        )
        explorer_label.pack(fill="x", padx=8, pady=2)  # Reduced padding
        
        explorer_desc = ctk.CTkLabel(
            explorer_frame,
            text="Fix unresponsive taskbar or desktop",
            font=ctk.CTkFont(size=10),  # Smaller font
            text_color="gray",
            anchor="w"
        )
        explorer_desc.pack(fill="x", padx=8, pady=0)
        
        restart_explorer_btn = ctk.CTkButton(
            explorer_frame,
            text="Restart Explorer",
            command=self.restart_explorer,
            height=26,  # Reduced height
            font=ctk.CTkFont(size=11)  # Smaller font
        )
        restart_explorer_btn.pack(padx=8, pady=5)  # Reduced padding
        
        # Reset Network
        network_frame = ctk.CTkFrame(utilities_scroll)
        network_frame.pack(fill="x", padx=2, pady=2)  # Reduced padding
        
        network_label = ctk.CTkLabel(
            network_frame,
            text="Reset Network Adapter",
            font=ctk.CTkFont(size=12, weight="bold"),  # Smaller font
            anchor="w"
        )
        network_label.pack(fill="x", padx=8, pady=2)  # Reduced padding
        
        network_desc = ctk.CTkLabel(
            network_frame,
            text="Fix connectivity issues",
            font=ctk.CTkFont(size=10),  # Smaller font
            text_color="gray",
            anchor="w"
        )
        network_desc.pack(fill="x", padx=8, pady=0)
        
        reset_network_btn = ctk.CTkButton(
            network_frame,
            text="Reset Network",
            command=self.reset_network,
            height=26,  # Reduced height
            font=ctk.CTkFont(size=11)  # Smaller font
        )
        reset_network_btn.pack(padx=8, pady=5)  # Reduced padding
        
        # System info
        sysinfo_frame = ctk.CTkFrame(utilities_scroll)
        sysinfo_frame.pack(fill="x", padx=2, pady=2)  # Reduced padding
        
        sysinfo_label = ctk.CTkLabel(
            sysinfo_frame,
            text="System Information",
            font=ctk.CTkFont(size=12, weight="bold"),  # Smaller font
            anchor="w"
        )
        sysinfo_label.pack(fill="x", padx=8, pady=2)  # Reduced padding
        
        sysinfo_desc = ctk.CTkLabel(
            sysinfo_frame,
            text="View detailed system information",
            font=ctk.CTkFont(size=10),  # Smaller font
            text_color="gray",
            anchor="w"
        )
        sysinfo_desc.pack(fill="x", padx=8, pady=0)
        
        sysinfo_btn = ctk.CTkButton(
            sysinfo_frame,
            text="Show System Info",
            command=self.show_system_info,
            height=26,  # Reduced height
            font=ctk.CTkFont(size=11)  # Smaller font
        )
        sysinfo_btn.pack(padx=8, pady=5)  # Reduced padding
        
        # Add a quick note section (more compact version)
        notes_frame = ctk.CTkFrame(utilities_scroll)
        notes_frame.pack(fill="x", padx=2, pady=2)  # Reduced padding
        
        notes_label = ctk.CTkLabel(
            notes_frame,
            text="Quick Notes",
            font=ctk.CTkFont(size=12, weight="bold"),  # Smaller font
            anchor="w"
        )
        notes_label.pack(fill="x", padx=8, pady=2)  # Reduced padding
        
        self.notes_text = ctk.CTkTextbox(
            notes_frame,
            height=60,  # Reduced height
            font=ctk.CTkFont(family="Segoe UI", size=10)  # Smaller font
        )
        self.notes_text.pack(fill="x", padx=8, pady=2)  # Reduced padding
        
        notes_buttons_frame = ctk.CTkFrame(notes_frame, fg_color="transparent")
        notes_buttons_frame.pack(fill="x", padx=8, pady=2)  # Reduced padding
        
        save_notes_btn = ctk.CTkButton(
            notes_buttons_frame,
            text="Save",
            command=self.save_notes,
            width=60,  # Reduced width
            height=24,  # Reduced height
            font=ctk.CTkFont(size=11)  # Smaller font
        )
        save_notes_btn.pack(side="left", padx=2, pady=2)  # Reduced padding
        
        clear_notes_btn = ctk.CTkButton(
            notes_buttons_frame,
            text="Clear",
            command=self.clear_notes,
            fg_color="gray",
            width=60,  # Reduced width
            height=24,  # Reduced height
            font=ctk.CTkFont(size=11)  # Smaller font
        )
        clear_notes_btn.pack(side="left", padx=2, pady=2)  # Reduced padding
        
        # Try to fetch weather on startup
        self.after(1000, self.fetch_weather)
    
    def edit_schedule(self):
        """Opens dialog to edit class schedule"""
        # This would be implemented to allow editing of schedule data
        self.show_message("Info", "Schedule editing will be implemented in a future update.")
    
    def fetch_weather(self):
        """Fetches weather data from OpenWeatherMap API"""
        try:
            import requests
            import json
            from datetime import datetime
            
            city = self.location_var.get()
            if not city:
                city = "New York"  # Default city
                
            # This would use a real API key in production
            # For now, we'll simulate the response
            
            # Simulated weather data
            weather_data = {
                "main": {
                    "temp": 22.5,
                    "humidity": 65
                },
                "weather": [
                    {
                        "main": "Partly Cloudy",
                        "description": "partly cloudy with occasional sun"
                    }
                ],
                "wind": {
                    "speed": 12
                },
                "name": city
            }
            
            # Update UI with weather data
            temp = round(weather_data["main"]["temp"])
            self.temperature_label.configure(text=f"{temp} °C")
            
            condition = weather_data["weather"][0]["main"]
            self.condition_label.configure(text=f"{condition}")
            
            # Set weather icon based on condition
            if "clear" in condition.lower():
                self.weather_icon_label.configure(text="☀️")
            elif "cloud" in condition.lower():
                self.weather_icon_label.configure(text="🌤️")
            elif "rain" in condition.lower():
                self.weather_icon_label.configure(text="🌧️")
            elif "snow" in condition.lower():
                self.weather_icon_label.configure(text="❄️")
            elif "thunder" in condition.lower():
                self.weather_icon_label.configure(text="⛈️")
            elif "mist" in condition.lower() or "fog" in condition.lower():
                self.weather_icon_label.configure(text="🌫️")
            else:
                self.weather_icon_label.configure(text="🌡️")
                
            # Update details
            self.humidity_label.configure(text=f"Humidity: {weather_data['main']['humidity']}%")
            self.wind_label.configure(text=f"Wind: {weather_data['wind']['speed']} km/h")
            
            # Update last updated time
            now = datetime.now().strftime("%H:%M:%S")
            self.last_updated_label.configure(text=f"Last updated: {now}")
            
        except Exception as e:
            print(f"Error fetching weather: {e}")
            self.temperature_label.configure(text="-- °C")
            self.condition_label.configure(text="Weather data unavailable")
            self.weather_icon_label.configure(text="❓")
    
    def restart_explorer(self):
        """Restarts Windows Explorer process"""
        try:
            import subprocess
            import threading
            
            def restart_process():
                # Kill explorer process
                subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Start explorer again
                subprocess.Popen(["explorer.exe"], shell=True)
                
                # Update UI from main thread
                self.after(0, lambda: self.show_message("Success", "Windows Explorer has been restarted"))
            
            # Run in separate thread to avoid freezing UI
            threading.Thread(target=restart_process).start()
            
        except Exception as e:
            self.show_message("Error", f"Failed to restart Explorer: {e}")
    
    def reset_network(self):
        """Resets network adapters"""
        try:
            import subprocess
            import threading
            
            def reset_network_process():
                # Disable and enable network adapters
                subprocess.run(["ipconfig", "/release"], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["ipconfig", "/flushdns"], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["ipconfig", "/renew"], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Update UI from main thread
                self.after(0, lambda: self.show_message("Success", "Network has been reset"))
            
            # Run in separate thread to avoid freezing UI
            threading.Thread(target=reset_network_process).start()
            
        except Exception as e:
            self.show_message("Error", f"Failed to reset network: {e}")
    
    def show_system_info(self):
        """Shows system information"""
        try:
            import platform
            import psutil
            
            # Get system information
            system = platform.system()
            release = platform.release()
            version = platform.version()
            processor = platform.processor()
            
            # Get memory information
            memory = psutil.virtual_memory()
            memory_total = round(memory.total / (1024.0 ** 3), 2)  # Convert to GB
            memory_used = round(memory.used / (1024.0 ** 3), 2)    # Convert to GB
            memory_percent = memory.percent
            
            # Get disk information
            disk = psutil.disk_usage('/')
            disk_total = round(disk.total / (1024.0 ** 3), 2)      # Convert to GB
            disk_used = round(disk.used / (1024.0 ** 3), 2)        # Convert to GB
            disk_percent = disk.percent
            
            # Format system info message
            info_message = f"System: {system} {release}\n"
            info_message += f"Version: {version}\n"
            info_message += f"Processor: {processor}\n\n"
            info_message += f"Memory: {memory_used} GB / {memory_total} GB ({memory_percent}%)\n"
            info_message += f"Disk: {disk_used} GB / {disk_total} GB ({disk_percent}%)"
            
            # Show system info in a dialog
            self.show_message("System Information", info_message)
            
        except ImportError:
            self.show_message("Error", "Required module not found. Please install 'psutil' package.")
        except Exception as e:
            self.show_message("Error", f"Failed to get system info: {e}")
    
    def save_notes(self):
        """Saves quick notes to a file"""
        try:
            notes_content = self.notes_text.get("1.0", "end-1c")
            
            if not notes_content.strip():
                self.show_message("Error", "No notes to save")
                return
                
            from datetime import datetime
            import os
            
            # Create notes directory if it doesn't exist
            if not os.path.exists("notes"):
                os.makedirs("notes")
                
            # Save notes with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"notes/note_{timestamp}.txt"
            
            with open(filename, "w") as f:
                f.write(notes_content)
                
            self.show_message("Success", f"Notes saved to {filename}")
            
        except Exception as e:
            self.show_message("Error", f"Failed to save notes: {e}")
    
    def clear_notes(self):
        """Clears the notes text box"""
        self.notes_text.delete("1.0", "end")
        
    def create_schedule_grid(self):
        """Creates a grid-based schedule view with clickable subjects"""
        # Clear existing widgets if any
        for widget in self.schedule_container.winfo_children():
            widget.destroy()
            
        # Define days of the week
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        # Define time slots - 4 periods before lunch, lunch, 4 periods after lunch (with one empty)
        time_slots = [
            {"period": 1, "time": "8:30 - 9:20", "type": "class"},
            {"period": 2, "time": "9:30 - 10:20", "type": "class"},
            {"period": 3, "time": "10:30 - 11:20", "type": "class"},
            {"period": 4, "time": "11:30 - 12:20", "type": "class"},
            {"period": "Lunch", "time": "12:30 - 1:20", "type": "lunch"},
            {"period": 5, "time": "1:30 - 2:20", "type": "class"},
            {"period": 6, "time": "2:30 - 3:20", "type": "class"},
            {"period": 7, "time": "3:30 - 4:20", "type": "class"},
            {"period": 8, "time": "", "type": "empty"}  # Empty period
        ]
        
        # Define subject colors
        subject_colors = {
            "Mathematics": {"bg": "#b388ff", "text": "#000000"},     # Purple
            "Physics": {"bg": "#7fdbff", "text": "#000000"},        # Light blue
            "Computer Science": {"bg": "#ff6b6b", "text": "#000000"}, # Red
            "English": {"bg": "#ffb74d", "text": "#000000"},        # Orange
            "Chemistry": {"bg": "#aed581", "text": "#000000"},      # Green
            "Biology": {"bg": "#4db6ac", "text": "#000000"},        # Teal
            "History": {"bg": "#f48fb1", "text": "#000000"},        # Pink
            "Geography": {"bg": "#90a4ae", "text": "#000000"},      # Blue Gray
            "Art": {"bg": "#ffe082", "text": "#000000"},           # Amber
            "Physical Education": {"bg": "#e0e0e0", "text": "#000000"}, # Gray
        }
        
        # Sample schedule data - this would be loaded from a file in a real implementation
        self.schedule_data = {
            "Monday": {
                "8:30 - 9:20": {"subject": "Mathematics", "teacher": "Dr. Smith"},
                "9:30 - 10:20": {"subject": "Physics", "teacher": "Dr. Johnson"},
                "10:30 - 11:20": {"subject": "English", "teacher": "Ms. Davis"},
                "11:30 - 12:20": {"subject": "Computer Science", "teacher": "Prof. Wilson"},
                "1:30 - 2:20": {"subject": "Chemistry", "teacher": "Dr. Roberts"},
                "2:30 - 3:20": {"subject": "History", "teacher": "Prof. Adams"},
                "3:30 - 4:20": {"subject": "Biology", "teacher": "Dr. Thompson"}
            },
            "Tuesday": {
                "8:30 - 9:20": {"subject": "Physics", "teacher": "Dr. Johnson"},
                "9:30 - 10:20": {"subject": "Mathematics", "teacher": "Dr. Smith"},
                "10:30 - 11:20": {"subject": "Computer Science", "teacher": "Prof. Wilson"},
                "11:30 - 12:20": {"subject": "English", "teacher": "Ms. Davis"},
                "1:30 - 2:20": {"subject": "History", "teacher": "Prof. Adams"},
                "2:30 - 3:20": {"subject": "Chemistry", "teacher": "Dr. Roberts"},
                "3:30 - 4:20": {"subject": "Physical Education", "teacher": "Coach Brown"}
            },
            "Wednesday": {
                "8:30 - 9:20": {"subject": "Biology", "teacher": "Dr. Thompson"},
                "9:30 - 10:20": {"subject": "Chemistry", "teacher": "Dr. Roberts"},
                "10:30 - 11:20": {"subject": "Mathematics", "teacher": "Dr. Smith"},
                "11:30 - 12:20": {"subject": "History", "teacher": "Prof. Adams"},
                "1:30 - 2:20": {"subject": "English", "teacher": "Ms. Davis"},
                "2:30 - 3:20": {"subject": "Computer Science", "teacher": "Prof. Wilson"},
                "3:30 - 4:20": {"subject": "Physics", "teacher": "Dr. Johnson"}
            },
            "Thursday": {
                "8:30 - 9:20": {"subject": "Computer Science", "teacher": "Prof. Wilson"},
                "9:30 - 10:20": {"subject": "English", "teacher": "Ms. Davis"},
                "10:30 - 11:20": {"subject": "Physics", "teacher": "Dr. Johnson"},
                "11:30 - 12:20": {"subject": "Mathematics", "teacher": "Dr. Smith"},
                "1:30 - 2:20": {"subject": "Biology", "teacher": "Dr. Thompson"},
                "2:30 - 3:20": {"subject": "Art", "teacher": "Ms. Parker"},
                "3:30 - 4:20": {"subject": "Physical Education", "teacher": "Coach Brown"}
            },
            "Friday": {
                "8:30 - 9:20": {"subject": "History", "teacher": "Prof. Adams"},
                "9:30 - 10:20": {"subject": "Geography", "teacher": "Dr. Garcia"},
                "10:30 - 11:20": {"subject": "Computer Science", "teacher": "Prof. Wilson"},
                "11:30 - 12:20": {"subject": "Biology", "teacher": "Dr. Thompson"},
                "1:30 - 2:20": {"subject": "Physics", "teacher": "Dr. Johnson"},
                "2:30 - 3:20": {"subject": "Mathematics", "teacher": "Dr. Smith"},
                "3:30 - 4:20": {"subject": "English", "teacher": "Ms. Davis"}
            },
            "Saturday": {
                "8:30 - 9:20": {"subject": "Art", "teacher": "Ms. Parker"},
                "9:30 - 10:20": {"subject": "Physical Education", "teacher": "Coach Brown"},
                "10:30 - 11:20": None,
                "11:30 - 12:20": None,
                "1:30 - 2:20": None,
                "2:30 - 3:20": None,
                "3:30 - 4:20": None
            }
        }
        
        # Set the schedule frame to fixed height to prevent excessive expansion
        self.schedule_container.configure(height=660)  # Reduced height (was previously unconstrained)
        
        # Create time period labels on the left
        for i, time_slot in enumerate(time_slots):
            # Create time label frame
            time_frame = ctk.CTkFrame(self.schedule_container, fg_color="transparent", height=60)  # Fixed height
            time_frame.grid(row=i+1, column=0, sticky="nsew", padx=1, pady=0)  # Reduced padding
            
            # Add time label
            if time_slot["type"] != "lunch":
                time_label = ctk.CTkLabel(
                    time_frame,
                    text=time_slot["time"],
                    font=ctk.CTkFont(size=10),  # Smaller font
                    width=90,  # Narrower
                    anchor="e"
                )
                time_label.pack(side="left", padx=2, pady=2)  # Reduced padding
                
                # Add period label if it's a class period
                if time_slot["type"] == "class":
                    period_label = ctk.CTkLabel(
                        time_frame,
                        text=f"P{time_slot['period']}",  # Shorter text
                        font=ctk.CTkFont(size=10, weight="bold"),  # Smaller font
                        anchor="w"
                    )
                    period_label.pack(side="right", padx=2, pady=2)  # Reduced padding
        
        # Add day headers
        for i, day in enumerate(days):
            day_frame = ctk.CTkFrame(self.schedule_container, fg_color="#f0f0f0", height=30)  # Fixed height
            day_frame.grid(row=0, column=i+1, sticky="nsew", padx=1, pady=0)  # Reduced padding
            
            day_label = ctk.CTkLabel(
                day_frame,
                text=day,
                font=ctk.CTkFont(size=12, weight="bold"),  # Smaller font
                text_color="#333333"
            )
            day_label.pack(pady=4)  # Reduced padding
            
            # Highlight current day
            if day == datetime.now().strftime("%A"):
                day_frame.configure(fg_color="#e3f2fd")
                day_label.configure(text_color="#1976d2")
                
        # Add lunch row
        lunch_row = time_slots.index(next((ts for ts in time_slots if ts["type"] == "lunch"), None)) + 1
        lunch_frame = ctk.CTkFrame(self.schedule_container, fg_color="#000000", height=30)  # Fixed height
        lunch_frame.grid(row=lunch_row, column=1, columnspan=len(days), sticky="nsew", padx=1, pady=0)  # Reduced padding
        
        lunch_label = ctk.CTkLabel(
            lunch_frame,
            text="LUNCH (12:30 - 1:20 PM)",
            font=ctk.CTkFont(size=12, weight="bold"),  # Smaller font
            text_color="#ffffff"
        )
        lunch_label.pack(pady=4)  # Reduced padding
            
        # Add schedule grid for each day and time slot
        for i, time_slot in enumerate(time_slots):
            # Skip lunch row as we've already added it
            if time_slot["type"] == "lunch":
                continue
                
            # Add cells for each day
            for day_idx, day in enumerate(days):
                # Create a cell for this day and time
                if time_slot["time"] in self.schedule_data.get(day, {}) and self.schedule_data[day][time_slot["time"]] is not None:
                    class_data = self.schedule_data[day][time_slot["time"]]
                    
                    # Get colors for the subject
                    colors = subject_colors.get(class_data["subject"], {"bg": "#e0e0e0", "text": "#000000"})
                    
                    # Create class cell
                    class_frame = ctk.CTkFrame(
                        self.schedule_container, 
                        fg_color=colors["bg"],
                        corner_radius=0,
                        height=60  # Fixed height
                    )
                    class_frame.grid(
                        row=i+1, 
                        column=day_idx+1, 
                        sticky="nsew",
                        padx=1, pady=0  # Reduced padding
                    )
                    
                    # Add subject label
                    subject_label = ctk.CTkLabel(
                        class_frame,
                        text=class_data["subject"],
                        font=ctk.CTkFont(size=11, weight="bold"),  # Smaller font
                        text_color=colors["text"]
                    )
                    subject_label.pack(anchor="center", padx=2, pady=(2, 0))  # Reduced padding
                    
                    # Add teacher label
                    teacher_label = ctk.CTkLabel(
                        class_frame,
                        text=class_data["teacher"],
                        font=ctk.CTkFont(size=9),  # Smaller font
                        text_color=colors["text"]
                    )
                    teacher_label.pack(anchor="center", padx=2, pady=(0, 2))  # Reduced padding
                    
                    # Make the class cell clickable
                    class_frame.bind("<Button-1>", lambda e, d=day, t=time_slot["time"]: 
                                    self.show_class_details(d, t))
                    subject_label.bind("<Button-1>", lambda e, d=day, t=time_slot["time"]: 
                                      self.show_class_details(d, t))
                    teacher_label.bind("<Button-1>", lambda e, d=day, t=time_slot["time"]: 
                                      self.show_class_details(d, t))
                else:
                    # Create empty cell
                    empty_frame = ctk.CTkFrame(
                        self.schedule_container, 
                        fg_color="transparent",
                        height=60  # Fixed height
                    )
                    empty_frame.grid(
                        row=i+1, 
                        column=day_idx+1, 
                        sticky="nsew",
                        padx=1, pady=0  # Reduced padding
                    )
                    
                    # Make empty cell clickable to add a class
                    if time_slot["type"] != "empty":  # Don't allow adding classes to the empty row
                        empty_frame.bind("<Button-1>", lambda e, d=day, t=time_slot["time"]: 
                                        self.add_new_class(d, t))
        
        # Configure row and column weights to make cells expand properly
        # But ensure they don't expand too much
        for i in range(len(time_slots) + 1):
            self.schedule_container.grid_rowconfigure(i, weight=0)  # Changed from 1 to 0 to prevent expansion
            
        for i in range(len(days) + 1):
            self.schedule_container.grid_columnconfigure(i, weight=1)
    
    def show_class_details(self, day, time_slot):
        """Shows a detailed card view for the selected class"""
        # Get class data
        class_data = self.schedule_data[day][time_slot]
        
        # Create popup window for class details
        self.class_popup = ctk.CTkToplevel(self)
        self.class_popup.title(f"{class_data['subject']} Details")
        self.class_popup.geometry("400x520")
        self.class_popup.resizable(False, False)
        self.class_popup.grab_set()  # Make window modal
        
        # Subject colors for selection
        subject_colors = {
            "Purple": "#b388ff",
            "Blue": "#7fdbff",
            "Red": "#ff6b6b",
            "Orange": "#ffb74d",
            "Green": "#aed581",
            "Teal": "#4db6ac",
            "Pink": "#f48fb1",
            "Blue Gray": "#90a4ae",
            "Amber": "#ffe082",
            "Gray": "#e0e0e0"
        }
        
        # Add subject header
        self.current_color = next((color for color_name, color in subject_colors.items() 
                               if color == self.get_subject_color(class_data["subject"])), "#3b82f6")
        
        subject_frame = ctk.CTkFrame(self.class_popup, fg_color=self.current_color, corner_radius=0)
        subject_frame.pack(fill="x", padx=0, pady=0)
        
        # Add day and time information
        day_time_label = ctk.CTkLabel(
            subject_frame,
            text=f"{day}, {time_slot}",
            font=ctk.CTkFont(size=12),
            text_color="#000000" if self.is_light_color(self.current_color) else "#ffffff"
        )
        day_time_label.pack(pady=(10, 0))
        
        # Subject label
        subject_label = ctk.CTkLabel(
            subject_frame,
            text=class_data["subject"],
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#000000" if self.is_light_color(self.current_color) else "#ffffff"
        )
        subject_label.pack(pady=(0, 20))
        
        # Details container
        details_frame = ctk.CTkFrame(self.class_popup)
        details_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Class details
        info_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Subject
        subject_label = ctk.CTkLabel(
            info_frame,
            text="Subject:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        subject_label.grid(row=0, column=0, padx=5, pady=10, sticky="e")
        
        self.subject_var = tk.StringVar(value=class_data["subject"])
        subject_entry = ctk.CTkEntry(
            info_frame,
            textvariable=self.subject_var,
            width=200
        )
        subject_entry.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        # Teacher
        teacher_label = ctk.CTkLabel(
            info_frame,
            text="Teacher:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        teacher_label.grid(row=1, column=0, padx=5, pady=10, sticky="e")
        
        self.teacher_var = tk.StringVar(value=class_data["teacher"])
        teacher_entry = ctk.CTkEntry(
            info_frame,
            textvariable=self.teacher_var,
            width=200
        )
        teacher_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        
        # Color selection
        color_label = ctk.CTkLabel(
            info_frame,
            text="Color:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        color_label.grid(row=2, column=0, padx=5, pady=10, sticky="e")
        
        # Color option menu
        self.color_var = tk.StringVar(value=next((name for name, color in subject_colors.items() 
                                             if color == self.get_subject_color(class_data["subject"])), "Blue"))
        
        color_dropdown = ctk.CTkOptionMenu(
            info_frame,
            values=list(subject_colors.keys()),
            variable=self.color_var,
            width=200,
            command=lambda x: self.update_card_color(subject_colors[x])
        )
        color_dropdown.grid(row=2, column=1, padx=5, pady=10, sticky="w")
        
        # Room number
        room_label = ctk.CTkLabel(
            info_frame,
            text="Room:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        room_label.grid(row=3, column=0, padx=5, pady=10, sticky="e")
        
        self.room_var = tk.StringVar(value=class_data.get("room", ""))
        room_entry = ctk.CTkEntry(
            info_frame,
            textvariable=self.room_var,
            width=200
        )
        room_entry.grid(row=3, column=1, padx=5, pady=10, sticky="w")
        
        # Notes
        notes_label = ctk.CTkLabel(
            details_frame,
            text="Notes:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        notes_label.pack(anchor="w", padx=10, pady=(20, 5))
        
        self.notes_text = ctk.CTkTextbox(
            details_frame,
            height=100,
            width=350
        )
        self.notes_text.pack(fill="x", padx=10, pady=5)
        
        # Add initial text if there are notes
        if "notes" in class_data:
            self.notes_text.insert("1.0", class_data["notes"])
        
        # Buttons
        buttons_frame = ctk.CTkFrame(self.class_popup, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        save_button = ctk.CTkButton(
            buttons_frame,
            text="Save Changes",
            command=lambda: self.save_class_changes(
                day,
                time_slot,
                self.subject_var.get(),
                self.teacher_var.get(),
                self.room_var.get(),
                self.notes_text.get("1.0", "end-1c"),
                self.color_var.get()
            )
        )
        save_button.pack(side="left", padx=10)
        
        delete_button = ctk.CTkButton(
            buttons_frame,
            text="Delete Class",
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=lambda: self.delete_class(day, time_slot)
        )
        delete_button.pack(side="right", padx=10)
    
    def update_card_color(self, color_hex):
        """Updates the color of the subject card in real-time"""
        if hasattr(self, 'class_popup') and hasattr(self, 'current_color'):
            # Find the subject frame which is the first child of the popup
            subject_frame = self.class_popup.winfo_children()[0]
            if isinstance(subject_frame, ctk.CTkFrame):
                subject_frame.configure(fg_color=color_hex)
                self.current_color = color_hex
                
                # Update text color based on background color
                text_color = "#000000" if self.is_light_color(color_hex) else "#ffffff"
                
                # Update the text color of all labels in the subject frame
                for widget in subject_frame.winfo_children():
                    if isinstance(widget, ctk.CTkLabel):
                        widget.configure(text_color=text_color)
    
    def is_light_color(self, hex_color):
        """Determines if a color is light or dark based on hex value"""
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) if len(hex_color) == 6 else (128, 128, 128)
        
        # Calculate luminance - ITU-R BT.709 formula
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Return True if color is light
        return luminance > 0.5
    
    def get_subject_color(self, subject):
        """Gets the color associated with a subject"""
        subject_colors = {
            "Mathematics": "#b388ff",     # Purple
            "Physics": "#7fdbff",        # Light blue
            "Computer Science": "#ff6b6b", # Red
            "English": "#ffb74d",        # Orange
            "Chemistry": "#aed581",      # Green
            "Biology": "#4db6ac",        # Teal
            "History": "#f48fb1",        # Pink
            "Geography": "#90a4ae",      # Blue Gray
            "Art": "#ffe082",           # Amber
            "Physical Education": "#e0e0e0", # Gray
        }
        
        return subject_colors.get(subject, "#e0e0e0")
    
    def save_class_changes(self, day, time_slot, subject, teacher, room, notes, color_name):
        """Saves changes made to a class"""
        # Get color hex value
        subject_colors = {
            "Purple": "#b388ff",
            "Blue": "#7fdbff",
            "Red": "#ff6b6b",
            "Orange": "#ffb74d",
            "Green": "#aed581",
            "Teal": "#4db6ac",
            "Pink": "#f48fb1",
            "Blue Gray": "#90a4ae",
            "Amber": "#ffe082",
            "Gray": "#e0e0e0"
        }
        
        # Update the global subject color mapping if the subject name has changed
        old_subject = self.schedule_data[day][time_slot]["subject"]
        
        # Update class data
        self.schedule_data[day][time_slot] = {
            "subject": subject,
            "teacher": teacher,
            "room": room,
            "notes": notes,
            "color": subject_colors.get(color_name, "#e0e0e0")
        }
        
        # Close popup
        self.class_popup.destroy()
        
        # Refresh the schedule grid
        self.create_schedule_grid()
        
        # Show message
        self.show_message("Success", f"Changes to {subject} saved successfully")
    
    def delete_class(self, day, time_slot):
        """Deletes a class from the schedule"""
        # Get the subject name before deleting
        subject = self.schedule_data[day][time_slot]["subject"]
        
        # Remove the class from schedule_data
        self.schedule_data[day][time_slot] = None
        
        # Close popup
        self.class_popup.destroy()
        
        # Refresh the schedule grid
        self.create_schedule_grid()
        
        # Show message
        self.show_message("Success", f"{subject} removed from schedule")
    
    def add_new_class(self, day, time_slot):
        """Opens a dialog to add a new class to the schedule"""
        # Create popup window for adding a new class
        self.add_class_popup = ctk.CTkToplevel(self)
        self.add_class_popup.title("Add New Class")
        self.add_class_popup.geometry("400x520")
        self.add_class_popup.resizable(False, False)
        self.add_class_popup.grab_set()  # Make window modal
        
        # Subject colors for selection
        subject_colors = {
            "Purple": "#b388ff",
            "Blue": "#7fdbff",
            "Red": "#ff6b6b",
            "Orange": "#ffb74d",
            "Green": "#aed581",
            "Teal": "#4db6ac",
            "Pink": "#f48fb1",
            "Blue Gray": "#90a4ae",
            "Amber": "#ffe082",
            "Gray": "#e0e0e0"
        }
        
        # Add header
        header_frame = ctk.CTkFrame(self.add_class_popup, fg_color="#3b82f6", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        # Add day and time information
        day_time_label = ctk.CTkLabel(
            header_frame,
            text=f"{day}, {time_slot}",
            font=ctk.CTkFont(size=12),
            text_color="#ffffff"
        )
        day_time_label.pack(pady=(10, 0))
        
        header_label = ctk.CTkLabel(
            header_frame,
            text="Add New Class",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        header_label.pack(pady=(0, 20))
        
        # Details container
        details_frame = ctk.CTkFrame(self.add_class_popup)
        details_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Class details
        info_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Subject
        subject_label = ctk.CTkLabel(
            info_frame,
            text="Subject:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        subject_label.grid(row=0, column=0, padx=5, pady=10, sticky="e")
        
        subjects = ["Mathematics", "Physics", "Computer Science", "English", 
                   "Chemistry", "Biology", "History", "Geography", "Art", "Physical Education"]
        
        self.subject_var = tk.StringVar(value=subjects[0])
        subject_dropdown = ctk.CTkOptionMenu(
            info_frame,
            values=subjects,
            variable=self.subject_var,
            width=200
        )
        subject_dropdown.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        # Teacher
        teacher_label = ctk.CTkLabel(
            info_frame,
            text="Teacher:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        teacher_label.grid(row=1, column=0, padx=5, pady=10, sticky="e")
        
        self.teacher_var = tk.StringVar()
        teacher_entry = ctk.CTkEntry(
            info_frame,
            textvariable=self.teacher_var,
            width=200
        )
        teacher_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        
        # Color selection
        color_label = ctk.CTkLabel(
            info_frame,
            text="Color:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        color_label.grid(row=2, column=0, padx=5, pady=10, sticky="e")
        
        self.color_var = tk.StringVar(value="Blue")
        color_dropdown = ctk.CTkOptionMenu(
            info_frame,
            values=list(subject_colors.keys()),
            variable=self.color_var,
            width=200
        )
        color_dropdown.grid(row=2, column=1, padx=5, pady=10, sticky="w")
        
        # Room number
        room_label = ctk.CTkLabel(
            info_frame,
            text="Room:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        room_label.grid(row=3, column=0, padx=5, pady=10, sticky="e")
        
        self.room_var = tk.StringVar()
        room_entry = ctk.CTkEntry(
            info_frame,
            textvariable=self.room_var,
            width=200
        )
        room_entry.grid(row=3, column=1, padx=5, pady=10, sticky="w")
        
        # Notes
        notes_label = ctk.CTkLabel(
            details_frame,
            text="Notes:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        notes_label.pack(anchor="w", padx=10, pady=(20, 5))
        
        notes_text = ctk.CTkTextbox(
            details_frame,
            height=100,
            width=350
        )
        notes_text.pack(fill="x", padx=10, pady=5)
        
        # Buttons
        buttons_frame = ctk.CTkFrame(self.add_class_popup, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        add_button = ctk.CTkButton(
            buttons_frame,
            text="Add Class",
            command=lambda: self.save_new_class(
                day,
                time_slot,
                self.subject_var.get(),
                self.teacher_var.get(),
                self.room_var.get(),
                notes_text.get("1.0", "end-1c"),
                self.color_var.get()
            )
        )
        add_button.pack(side="left", padx=10)
        
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            fg_color="#6b7280",
            hover_color="#4b5563",
            command=lambda: self.add_class_popup.destroy()
        )
        cancel_button.pack(side="right", padx=10)
    
    def save_new_class(self, day, time_slot, subject, teacher, room, notes, color_name):
        """Saves a new class to the schedule"""
        # Get color hex value
        subject_colors = {
            "Purple": "#b388ff",
            "Blue": "#7fdbff",
            "Red": "#ff6b6b",
            "Orange": "#ffb74d",
            "Green": "#aed581",
            "Teal": "#4db6ac",
            "Pink": "#f48fb1",
            "Blue Gray": "#90a4ae",
            "Amber": "#ffe082",
            "Gray": "#e0e0e0"
        }
        
        # Create new class data
        new_class = {
            "subject": subject,
            "teacher": teacher,
            "room": room,
            "notes": notes,
            "color": subject_colors.get(color_name, "#e0e0e0")
        }
        
        # Add the class to the schedule data
        if day not in self.schedule_data:
            self.schedule_data[day] = {}
        
        self.schedule_data[day][time_slot] = new_class
        
        # Close popup
        self.add_class_popup.destroy()
        
        # Refresh the schedule grid
        self.create_schedule_grid()
        
        # Show message
        self.show_message("Success", f"{subject} added to schedule")
        
    def edit_schedule(self):
        """Information about editing the schedule"""
        self.show_message("Schedule Editor", "Click on any class to edit details or empty space to add a new class.")

if __name__ == "__main__":
    # Check if matplotlib is installed
    try:
        import matplotlib
    except ImportError:
        print("Matplotlib not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
        
    # Start the application
    app = TurboLearnGUI()
    
    # Run the main loop
    app.mainloop() 


