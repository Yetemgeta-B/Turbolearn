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
        
        # Apply colorization to the output
        if "Clicked" in string or "Found" in string or "successful" in string:
            self.text_widget.insert("end", string, "success")
        elif "Error" in string or "Failed" in string or "Could not" in string:
            self.text_widget.insert("end", string, "error")
        elif "Waiting" in string or "Looking" in string:
            self.text_widget.insert("end", string, "info")
        else:
            self.text_widget.insert("end", string)
            
        self.text_widget.configure(state="disabled")
        self.text_widget.see("end")
        
    def flush(self):
        self.buffer = ""

class AccountInfo:
    def __init__(self):
        self.file_path = os.path.join(os.path.expanduser("~"), "turbolearn_accounts.json")
        self.accounts = self.load_accounts()
        
    def load_accounts(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except:
                return {"accounts": [], "statistics": {"success": 0, "failed": 0}}
        else:
            return {"accounts": [], "statistics": {"success": 0, "failed": 0}}
            
    def save_accounts(self):
        with open(self.file_path, "w") as f:
            json.dump(self.accounts, f)
            
    def add_account(self, first_name, last_name, email, password, url, success=True):
        account = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "url": url,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Success" if success else "Failed"
        }
        self.accounts["accounts"].append(account)
        
        # Update statistics
        if success:
            self.accounts["statistics"]["success"] += 1
        else:
            self.accounts["statistics"]["failed"] += 1
            
        self.save_accounts()
        
    def get_accounts(self):
        return self.accounts["accounts"]
        
    def get_statistics(self):
        return self.accounts["statistics"]

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
        
        # Authentication settings
        self.is_authenticated = False
        self.auth_password = "turbolearn123"  # Default password, change this
        
        # Initialize account tracker
        self.account_info = AccountInfo()
        
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
        
        # Left frame - Console output
        console_label = ctk.CTkLabel(left_frame, text="Console Output", font=ctk.CTkFont(size=16, weight="bold"))
        console_label.pack(pady=(0, 10))
        
        self.console = ctk.CTkTextbox(left_frame, width=700, height=600, font=ctk.CTkFont(family="Consolas", size=12))
        self.console.pack(fill="both", expand=True, padx=10, pady=10)
        self.console.configure(state="disabled")
        self.console.tag_config("success", foreground="green")
        self.console.tag_config("error", foreground="red")
        self.console.tag_config("info", foreground="blue")
        
        # Create a text redirect
        self.text_redirect = RedirectText(self.console)
        
        # Clear console button
        clear_console_button = ctk.CTkButton(
            left_frame,
            text="Clear Console",
            command=self.clear_console
        )
        clear_console_button.pack(pady=10)
        
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
        self.console.configure(state="disabled")
        
    def setup_dashboard_tab(self):
        # Create frame for dashboard
        self.dashboard_frame = ctk.CTkFrame(self.tab_dashboard)
        self.dashboard_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add title
        dashboard_title = ctk.CTkLabel(
            self.dashboard_frame, 
            text="Account Dashboard", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        dashboard_title.pack(pady=10)
        
        # Check authentication before showing personal data
        if not self.is_authenticated:
            # Show authentication prompt
            self.create_auth_panel()
        else:
            # Show dashboard content
            self.create_dashboard_content()
    
    def create_auth_panel(self):
        """Show authentication panel for accessing personal dashboard data"""
        self.auth_frame = ctk.CTkFrame(self.dashboard_frame)
        self.auth_frame.pack(fill="both", expand=True, padx=50, pady=50)
        
        auth_label = ctk.CTkLabel(
            self.auth_frame,
            text="Authentication Required",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        auth_label.pack(pady=(20, 10))
        
        info_label = ctk.CTkLabel(
            self.auth_frame,
            text="Account information is protected.\nPlease authenticate to view your data.",
            font=ctk.CTkFont(size=14),
            justify="center"
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
            width=200
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
        """Verify the entered password"""
        if self.password_var.get() == self.auth_password:
            # Password correct
            self.is_authenticated = True
            
            # Clear authentication panel
            self.auth_frame.destroy()
            
            # Show the dashboard content
            self.create_dashboard_content()
        else:
            # Show error message
            error_label = ctk.CTkLabel(
                self.auth_frame,
                text="Incorrect password. Please try again.",
                text_color="red",
                font=ctk.CTkFont(size=12)
            )
            error_label.pack(pady=5)
    
    def create_dashboard_content(self):
        """Show the actual dashboard content after authentication"""
        # Add refresh button
        refresh_button = ctk.CTkButton(
            self.dashboard_frame,
            text="Refresh Data",
            command=self.refresh_dashboard
        )
        refresh_button.pack(pady=10)
        
        # Create split view for table and detail view
        self.dashboard_split = ctk.CTkFrame(self.dashboard_frame)
        self.dashboard_split.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Table frame - left side
        self.table_frame = ctk.CTkFrame(self.dashboard_split)
        self.table_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=0)
        
        # Detail frame - right side (initially hidden)
        self.detail_frame = ctk.CTkFrame(self.dashboard_split)
        
        # Table headers
        headers = ["First Name", "Last Name", "Email", "Created", "Status"]
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
    
    def refresh_dashboard(self):
        # If not authenticated, don't load private data
        if not hasattr(self, 'account_scroll') or not self.is_authenticated:
            return
            
        # Clear existing widgets in scrollable frame
        for widget in self.account_scroll.winfo_children():
            widget.destroy()
            
        # Get accounts
        accounts = self.account_info.get_accounts()
        
        # Add accounts to table
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
            
            # Configure grid
            for j in range(5):
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
        status_frame = ctk.CTkFrame(fields_frame, fg_color=status_color)
        status_frame.pack(fill="x", padx=10, pady=10)
        
        status_label = ctk.CTkLabel(
            status_frame, 
            text=f"Status: {account['status']}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        status_label.pack(pady=10)
        
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
        
        delete_button = ctk.CTkButton(
            action_frame,
            text="Delete Account",
            command=lambda: self.delete_account(account),
            fg_color="red",
            hover_color="darkred"
        )
        delete_button.pack(fill="x", pady=5)
    
    def open_account(self, url):
        """Open the account URL in the default browser"""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            self.show_message("Error", f"Could not open URL: {str(e)}")
    
    def add_detail_field(self, parent, label_text, value, is_password=False, is_url=False):
        field_frame = ctk.CTkFrame(parent)
        field_frame.pack(fill="x", padx=10, pady=5)
        
        label = ctk.CTkLabel(
            field_frame, 
            text=f"{label_text}:",
            font=ctk.CTkFont(weight="bold")
        )
        label.pack(anchor="w", padx=5, pady=2)
        
        if is_password:
            # For password, add a reveal button
            value_frame = ctk.CTkFrame(field_frame)
            value_frame.pack(fill="x", padx=5, pady=2)
            
            hidden_value = "*" * len(value)
            password_var = tk.StringVar(value=hidden_value)
            
            password_label = ctk.CTkLabel(
                value_frame,
                textvariable=password_var,
                font=ctk.CTkFont(family="Consolas")
            )
            password_label.pack(side="left", anchor="w", padx=5)
            
            is_revealed = [False]  # Use list for mutable state in closure
            
            def toggle_reveal():
                is_revealed[0] = not is_revealed[0]
                if is_revealed[0]:
                    password_var.set(value)
                    reveal_button.configure(text="Hide")
                else:
                    password_var.set(hidden_value)
                    reveal_button.configure(text="Show")
            
            reveal_button = ctk.CTkButton(
                value_frame,
                text="Show",
                command=toggle_reveal,
                width=60,
                height=25
            )
            reveal_button.pack(side="right", padx=5)
            
        elif is_url:
            # For URL, make it clickable
            url_label = ctk.CTkLabel(
                field_frame,
                text=value[:30] + "..." if len(value) > 30 else value,
                text_color="blue",
                cursor="hand2"
            )
            url_label.pack(anchor="w", padx=5, pady=2)
            
            def open_url(event):
                import webbrowser
                webbrowser.open(value)
                
            url_label.bind("<Button-1>", open_url)
        else:
            # Regular value
            value_label = ctk.CTkLabel(
                field_frame,
                text=value,
                font=ctk.CTkFont(family="Consolas"),
                wraplength=250
            )
            value_label.pack(anchor="w", padx=5, pady=2)
            
        # Add copy button for all fields
        copy_button = ctk.CTkButton(
            field_frame,
            text="Copy",
            command=lambda: self.copy_to_clipboard(value),
            width=60,
            height=25
        )
        copy_button.pack(anchor="e", padx=5, pady=2)
    
    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.show_message("Copied", "Value copied to clipboard!")
    
    def copy_account_info(self, account):
        info = f"TurboLearn Account Information\n"
        info += f"---------------------------\n"
        info += f"First Name: {account['first_name']}\n"
        info += f"Last Name: {account['last_name']}\n"
        info += f"Email: {account['email']}\n"
        info += f"Password: {account['password']}\n"
        info += f"Created: {account['created_at']}\n"
        if "url" in account and account["url"]:
            info += f"URL: {account['url']}\n"
        info += f"Status: {account['status']}\n"
        
        self.clipboard_clear()
        self.clipboard_append(info)
        self.show_message("Copied", "Full account information copied to clipboard!")
    
    def delete_account(self, account):
        confirm = tk.messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete the account for {account['email']}?"
        )
        
        if confirm:
            # Find and remove the account
            accounts = self.account_info.accounts["accounts"]
            for i, acc in enumerate(accounts):
                if acc["email"] == account["email"] and acc["created_at"] == account["created_at"]:
                    # Update statistics
                    if acc["status"] == "Success":
                        self.account_info.accounts["statistics"]["success"] -= 1
                    else:
                        self.account_info.accounts["statistics"]["failed"] -= 1
                    
                    # Remove the account
                    accounts.pop(i)
                    break
                    
            # Save changes
            self.account_info.save_accounts()
            
            # Refresh UI
            self.refresh_dashboard()
            self.refresh_visualization()
            self.close_account_details()
            
            self.show_message("Account Deleted", "The account has been deleted.")
    
    def close_account_details(self):
        # Hide the detail frame
        self.detail_frame.pack_forget()
        self.account_detail = None
        
    def setup_visualization_tab(self):
        # Create frame for visualizations
        self.viz_frame = ctk.CTkFrame(self.tab_visualization)
        self.viz_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add title
        viz_title = ctk.CTkLabel(
            self.viz_frame, 
            text="Analytics", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        viz_title.pack(pady=10)
        
        # Add refresh button
        refresh_viz_button = ctk.CTkButton(
            self.viz_frame,
            text="Refresh Charts",
            command=self.refresh_visualization
        )
        refresh_viz_button.pack(pady=10)
        
        # Create frame for charts
        self.charts_frame = ctk.CTkFrame(self.viz_frame)
        self.charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Setup initial visualization
        self.refresh_visualization()
        
    def refresh_visualization(self):
        # Clear existing widgets
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
            dates = [datetime.strptime(acc["created_at"], "%Y-%m-%d %H:%M:%S") for acc in accounts]
            statuses = [1 if acc["status"] == "Success" else 0 for acc in accounts]
            
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
            # No data message
            no_data = ctk.CTkLabel(
                right_chart, 
                text="No data available yet.\nCreate accounts to see timeline.",
                font=ctk.CTkFont(size=14)
            )
            no_data.pack(pady=50)
            
    def setup_scheduler_tab(self):
        # Create scheduler frame
        self.scheduler_frame = ctk.CTkFrame(self.tab_scheduler)
        self.scheduler_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add title
        scheduler_title = ctk.CTkLabel(
            self.scheduler_frame, 
            text="Automation Scheduler", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        scheduler_title.pack(pady=10)
        
        # Create split view
        scheduler_split = ctk.CTkFrame(self.scheduler_frame)
        scheduler_split.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Scheduled tasks
        tasks_frame = ctk.CTkFrame(scheduler_split)
        tasks_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=0)
        
        tasks_label = ctk.CTkLabel(
            tasks_frame, 
            text="Scheduled Tasks", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        tasks_label.pack(pady=10)
        
        # Add task list with headers
        headers_frame = ctk.CTkFrame(tasks_frame)
        headers_frame.pack(fill="x", padx=10, pady=5)
        
        headers = ["Task Name", "Schedule", "Browser", "Status", "Actions"]
        for i, header in enumerate(headers):
            lbl = ctk.CTkLabel(headers_frame, text=header, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            headers_frame.grid_columnconfigure(i, weight=1)
        
        # Create scrollable frame for tasks
        self.tasks_scroll = ctk.CTkScrollableFrame(tasks_frame)
        self.tasks_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # No scheduled tasks message
        no_tasks_label = ctk.CTkLabel(
            self.tasks_scroll, 
            text="No scheduled tasks. Create one using the form on the right.", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        no_tasks_label.pack(pady=50)
        
        # Right side - Add new schedule
        schedule_form = ctk.CTkFrame(scheduler_split)
        schedule_form.pack(side="right", fill="both", expand=False, padx=(5, 0), pady=0, ipadx=10, ipady=10)
        schedule_form.configure(width=300)
        
        form_label = ctk.CTkLabel(
            schedule_form, 
            text="Create New Schedule", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        form_label.pack(pady=10)
        
        # Task name
        name_frame = ctk.CTkFrame(schedule_form)
        name_frame.pack(fill="x", padx=10, pady=5)
        
        name_label = ctk.CTkLabel(name_frame, text="Task Name:")
        name_label.pack(anchor="w", padx=10, pady=5)
        
        self.schedule_name = tk.StringVar(value="")
        name_entry = ctk.CTkEntry(
            name_frame,
            textvariable=self.schedule_name,
            placeholder_text="Daily Account Creation"
        )
        name_entry.pack(fill="x", padx=10, pady=5)
        
        # Schedule type
        type_frame = ctk.CTkFrame(schedule_form)
        type_frame.pack(fill="x", padx=10, pady=5)
        
        type_label = ctk.CTkLabel(type_frame, text="Schedule Type:")
        type_label.pack(anchor="w", padx=10, pady=5)
        
        self.schedule_type = tk.StringVar(value="once")
        
        types_frame = ctk.CTkFrame(type_frame)
        types_frame.pack(fill="x", padx=10, pady=5)
        
        once_radio = ctk.CTkRadioButton(
            types_frame, 
            text="Run Once", 
            variable=self.schedule_type, 
            value="once",
            command=self.update_schedule_form
        )
        once_radio.pack(anchor="w", padx=10, pady=5)
        
        daily_radio = ctk.CTkRadioButton(
            types_frame, 
            text="Run Daily", 
            variable=self.schedule_type, 
            value="daily",
            command=self.update_schedule_form
        )
        daily_radio.pack(anchor="w", padx=10, pady=5)
        
        weekly_radio = ctk.CTkRadioButton(
            types_frame, 
            text="Run Weekly", 
            variable=self.schedule_type, 
            value="weekly",
            command=self.update_schedule_form
        )
        weekly_radio.pack(anchor="w", padx=10, pady=5)
        
        # Date selection for "Run Once"
        self.date_frame = ctk.CTkFrame(schedule_form)
        self.date_frame.pack(fill="x", padx=10, pady=5)
        
        date_label = ctk.CTkLabel(self.date_frame, text="Date:")
        date_label.pack(anchor="w", padx=10, pady=5)
        
        # Create a simple date selector
        date_select_frame = ctk.CTkFrame(self.date_frame)
        date_select_frame.pack(fill="x", padx=10, pady=5)
        
        # Get current date
        current_date = datetime.now()
        
        # Year selector
        self.year_var = tk.StringVar(value=str(current_date.year))
        year_label = ctk.CTkLabel(date_select_frame, text="Year:")
        year_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        years = [str(y) for y in range(current_date.year, current_date.year + 5)]
        year_dropdown = ctk.CTkOptionMenu(
            date_select_frame,
            values=years,
            variable=self.year_var
        )
        year_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Month selector
        self.month_var = tk.StringVar(value=str(current_date.month))
        month_label = ctk.CTkLabel(date_select_frame, text="Month:")
        month_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        months = [str(m) for m in range(1, 13)]
        month_dropdown = ctk.CTkOptionMenu(
            date_select_frame,
            values=months,
            variable=self.month_var
        )
        month_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Day selector
        self.day_var = tk.StringVar(value=str(current_date.day))
        day_label = ctk.CTkLabel(date_select_frame, text="Day:")
        day_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        days = [str(d) for d in range(1, 32)]
        day_dropdown = ctk.CTkOptionMenu(
            date_select_frame,
            values=days,
            variable=self.day_var
        )
        day_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Set column weights for alignment
        date_select_frame.grid_columnconfigure(0, weight=1)
        date_select_frame.grid_columnconfigure(1, weight=3)
        
        # Weekly day selection for "Run Weekly"
        self.weekly_frame = ctk.CTkFrame(schedule_form)
        # Initially hidden
        
        weekly_label = ctk.CTkLabel(self.weekly_frame, text="Day of Week:")
        weekly_label.pack(anchor="w", padx=10, pady=5)
        
        self.day_of_week = tk.StringVar(value="Monday")
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        weekly_dropdown = ctk.CTkOptionMenu(
            self.weekly_frame,
            values=days_of_week,
            variable=self.day_of_week
        )
        weekly_dropdown.pack(fill="x", padx=10, pady=5)
        
        # Time selection for all types
        time_frame = ctk.CTkFrame(schedule_form)
        time_frame.pack(fill="x", padx=10, pady=5)
        
        time_label = ctk.CTkLabel(time_frame, text="Time:")
        time_label.pack(anchor="w", padx=10, pady=5)
        
        time_select_frame = ctk.CTkFrame(time_frame)
        time_select_frame.pack(fill="x", padx=10, pady=5)
        
        # Hour selector
        self.hour_var = tk.StringVar(value=str(current_date.hour))
        hour_label = ctk.CTkLabel(time_select_frame, text="Hour:")
        hour_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        hours = [str(h).zfill(2) for h in range(24)]
        hour_dropdown = ctk.CTkOptionMenu(
            time_select_frame,
            values=hours,
            variable=self.hour_var
        )
        hour_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Minute selector
        self.minute_var = tk.StringVar(value=str(current_date.minute))
        minute_label = ctk.CTkLabel(time_select_frame, text="Minute:")
        minute_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        minutes = [str(m).zfill(2) for m in range(60)]
        minute_dropdown = ctk.CTkOptionMenu(
            time_select_frame,
            values=minutes,
            variable=self.minute_var
        )
        minute_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Set column weights for alignment
        time_select_frame.grid_columnconfigure(0, weight=1)
        time_select_frame.grid_columnconfigure(1, weight=3)
        
        # Browser selection
        browser_frame = ctk.CTkFrame(schedule_form)
        browser_frame.pack(fill="x", padx=10, pady=5)
        
        browser_label = ctk.CTkLabel(browser_frame, text="Browser:")
        browser_label.pack(anchor="w", padx=10, pady=5)
        
        self.schedule_browser = tk.StringVar(value=list(self.browsers.keys())[0] if self.browsers else "chrome")
        
        browser_dropdown = ctk.CTkOptionMenu(
            browser_frame,
            values=list(browser.capitalize() for browser in self.browsers.keys()),
            variable=self.schedule_browser
        )
        browser_dropdown.pack(fill="x", padx=10, pady=5)
        
        # Number of accounts
        accounts_frame = ctk.CTkFrame(schedule_form)
        accounts_frame.pack(fill="x", padx=10, pady=5)
        
        accounts_label = ctk.CTkLabel(accounts_frame, text="Number of Accounts:")
        accounts_label.pack(anchor="w", padx=10, pady=5)
        
        self.schedule_accounts = tk.IntVar(value=1)
        accounts_slider_label = ctk.CTkLabel(
            accounts_frame, 
            text=f"Accounts: {self.schedule_accounts.get()}"
        )
        accounts_slider_label.pack(anchor="w", padx=10, pady=5)
        
        def update_accounts_label(value):
            self.schedule_accounts.set(int(value))
            accounts_slider_label.configure(text=f"Accounts: {self.schedule_accounts.get()}")
        
        accounts_slider = ctk.CTkSlider(
            accounts_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            command=update_accounts_label
        )
        accounts_slider.set(1)
        accounts_slider.pack(fill="x", padx=10, pady=5)
        
        # Create button
        create_button = ctk.CTkButton(
            schedule_form,
            text="Create Schedule",
            command=self.create_schedule,
            fg_color="green",
            hover_color="darkgreen"
        )
        create_button.pack(fill="x", padx=10, pady=20)
        
        # Initialize schedule form
        self.update_schedule_form()
        
        # Initialize scheduled task store
        self.scheduled_tasks = []
        self.load_scheduled_tasks()
    
    def update_schedule_form(self):
        schedule_type = self.schedule_type.get()
        
        # Show/hide frames based on schedule type
        if schedule_type == "once":
            self.date_frame.pack(fill="x", padx=10, pady=5)
            if self.weekly_frame.winfo_manager():
                self.weekly_frame.pack_forget()
        elif schedule_type == "weekly":
            if not self.weekly_frame.winfo_manager():
                self.weekly_frame.pack(fill="x", padx=10, pady=5)
                # Insert before time_frame
                self.weekly_frame.pack(after=self.date_frame)
            self.date_frame.pack_forget()
        else:  # daily
            self.date_frame.pack_forget()
            if self.weekly_frame.winfo_manager():
                self.weekly_frame.pack_forget()
    
    def create_schedule(self):
        # Validate form
        if not self.schedule_name.get():
            self.show_message("Error", "Please enter a task name")
            return
        
        # Get schedule time
        hour = int(self.hour_var.get())
        minute = int(self.minute_var.get())
        
        schedule_type = self.schedule_type.get()
        schedule_time = None
        
        if schedule_type == "once":
            # Get date components
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            
            try:
                schedule_time = datetime(year, month, day, hour, minute)
                if schedule_time < datetime.now():
                    self.show_message("Error", "Scheduled time must be in the future")
                    return
            except ValueError:
                self.show_message("Error", "Invalid date. Please check your selection.")
                return
                
        elif schedule_type == "weekly":
            day_of_week = self.day_of_week.get()
            # Store the day name for display
            schedule_time = day_of_week
            
        # Default for daily is None
        
        # Create task object
        task = {
            "name": self.schedule_name.get(),
            "type": schedule_type,
            "time": schedule_time,
            "hour": hour,
            "minute": minute,
            "browser": self.schedule_browser.get(),
            "accounts": self.schedule_accounts.get(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Active"
        }
        
        # Add to list and save
        self.scheduled_tasks.append(task)
        self.save_scheduled_tasks()
        
        # Refresh task list
        self.refresh_task_list()
        
        # Show confirmation
        self.show_message("Schedule Created", f"Task '{task['name']}' has been scheduled")
        
        # Reset form
        self.schedule_name.set("")
    
    def save_scheduled_tasks(self):
        # Save scheduled tasks to file
        file_path = os.path.join(os.path.expanduser("~"), "turbolearn_schedules.json")
        
        try:
            with open(file_path, "w") as f:
                json.dump({"tasks": self.scheduled_tasks}, f)
        except Exception as e:
            print(f"Error saving scheduled tasks: {str(e)}")
    
    def load_scheduled_tasks(self):
        # Load scheduled tasks from file
        file_path = os.path.join(os.path.expanduser("~"), "turbolearn_schedules.json")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.scheduled_tasks = data.get("tasks", [])
                    self.refresh_task_list()
            except Exception as e:
                print(f"Error loading scheduled tasks: {str(e)}")
                self.scheduled_tasks = []
        else:
            self.scheduled_tasks = []
    
    def refresh_task_list(self):
        # Clear existing tasks
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()
            
        if not self.scheduled_tasks:
            # No scheduled tasks message
            no_tasks_label = ctk.CTkLabel(
                self.tasks_scroll, 
                text="No scheduled tasks. Create one using the form on the right.", 
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_tasks_label.pack(pady=50)
            return
            
        # Add each task to the list
        for i, task in enumerate(self.scheduled_tasks):
            task_frame = ctk.CTkFrame(self.tasks_scroll)
            task_frame.pack(fill="x", padx=5, pady=5)
            
            # Format schedule text based on type
            if task["type"] == "once":
                if isinstance(task["time"], str):
                    # Convert stored string to datetime if needed
                    try:
                        schedule_datetime = datetime.strptime(task["time"], "%Y-%m-%d %H:%M:%S")
                        schedule_text = schedule_datetime.strftime("%Y-%m-%d %H:%M")
                    except:
                        schedule_text = f"{task['hour']}:{task['minute']}"
                else:
                    schedule_text = "One-time"
            elif task["type"] == "weekly":
                schedule_text = f"{task['time']} at {task['hour']}:{str(task['minute']).zfill(2)}"
            else:  # daily
                schedule_text = f"Daily at {task['hour']}:{str(task['minute']).zfill(2)}"
                
            # Task name
            name_label = ctk.CTkLabel(task_frame, text=task["name"], font=ctk.CTkFont(weight="bold"))
            name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
            
            # Schedule details
            schedule_label = ctk.CTkLabel(task_frame, text=schedule_text)
            schedule_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            # Browser
            browser_label = ctk.CTkLabel(task_frame, text=task["browser"])
            browser_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
            
            # Status
            status_label = ctk.CTkLabel(
                task_frame, 
                text=task["status"],
                text_color="green" if task["status"] == "Active" else "red"
            )
            status_label.grid(row=0, column=3, padx=5, pady=5, sticky="w")
            
            # Actions
            actions_frame = ctk.CTkFrame(task_frame)
            actions_frame.grid(row=0, column=4, padx=5, pady=5, sticky="e")
            
            # Run now button
            run_button = ctk.CTkButton(
                actions_frame,
                text="Run",
                command=lambda t=task: self.run_scheduled_task(t),
                width=60,
                height=25
            )
            run_button.pack(side="left", padx=5)
            
            # Delete button
            delete_button = ctk.CTkButton(
                actions_frame,
                text="Delete",
                command=lambda t=task: self.delete_scheduled_task(t),
                fg_color="red",
                hover_color="darkred",
                width=60,
                height=25
            )
            delete_button.pack(side="left", padx=5)
            
            # Configure grid
            task_frame.grid_columnconfigure(0, weight=2)  # Name gets more space
            task_frame.grid_columnconfigure(1, weight=2)  # Schedule gets more space
            task_frame.grid_columnconfigure(2, weight=1)
            task_frame.grid_columnconfigure(3, weight=1)
            task_frame.grid_columnconfigure(4, weight=1)
    
    def run_scheduled_task(self, task):
        # Check if already running
        if self.is_running:
            self.show_message("Already Running", "A task is already running. Please wait for it to complete.")
            return
            
        # Switch to automation tab
        self.tabview.set("Automation")
        
        # Set up parameters for the task
        self.selected_browser.set(task["browser"].lower())
        self.batch_mode.set(task["accounts"] > 1)
        self.batch_count.set(task["accounts"])
        
        # Start automation
        self.start_automation()
    
    def delete_scheduled_task(self, task):
        confirm = tk.messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete the scheduled task '{task['name']}'?"
        )
        
        if confirm:
            self.scheduled_tasks.remove(task)
            self.save_scheduled_tasks()
            self.refresh_task_list()
            
    def check_scheduled_tasks(self):
        """Check if any scheduled tasks need to be run and run them if needed."""
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.strftime("%A")  # Monday, Tuesday, etc.
        
        for task in self.scheduled_tasks:
            if task["status"] != "Active":
                continue
                
            run_task = False
            
            if task["type"] == "once":
                # For one-time tasks, check if it's time and hasn't run before
                if isinstance(task["time"], str):
                    try:
                        task_time = datetime.strptime(task["time"], "%Y-%m-%d %H:%M:%S")
                        if now >= task_time:
                            run_task = True
                            # Mark as complete after running
                            task["status"] = "Completed"
                    except:
                        pass
            elif task["type"] == "daily":
                # For daily tasks, check if the current hour and minute match
                task_hour = int(task["hour"])
                task_minute = int(task["minute"])
                
                if current_time.hour == task_hour and current_time.minute == task_minute:
                    run_task = True
            elif task["type"] == "weekly":
                # For weekly tasks, check if it's the right day and time
                task_day = task["time"]
                task_hour = int(task["hour"])
                task_minute = int(task["minute"])
                
                if current_weekday == task_day and current_time.hour == task_hour and current_time.minute == task_minute:
                    run_task = True
            
            if run_task and not self.is_running:
                print(f"Running scheduled task: {task['name']}")
                self.run_scheduled_task(task)
                break  # Only run one task at a time
        
        # Check again in 1 minute
        self.after(60000, self.check_scheduled_tasks)

    def setup_settings_tab(self):
        # Create frame for settings
        self.settings_frame = ctk.CTkFrame(self.tab_settings)
        self.settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add title
        settings_title = ctk.CTkLabel(
            self.settings_frame, 
            text="Settings", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        settings_title.pack(pady=10)
        
        # Theme section
        theme_frame = ctk.CTkFrame(self.settings_frame)
        theme_frame.pack(fill="x", padx=10, pady=10)
        
        theme_label = ctk.CTkLabel(
            theme_frame, 
            text="Appearance", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        theme_label.pack(anchor="w", padx=10, pady=10)
        
        # Theme mode option menu
        appearance_mode_label = ctk.CTkLabel(theme_frame, text="Appearance Mode:")
        appearance_mode_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        appearance_mode_menu = ctk.CTkOptionMenu(
            theme_frame, 
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode
        )
        appearance_mode_menu.pack(anchor="w", padx=20, pady=10)
        
        # UI Scale option menu
        ui_scale_label = ctk.CTkLabel(theme_frame, text="UI Scaling:")
        ui_scale_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        ui_scale_menu = ctk.CTkOptionMenu(
            theme_frame, 
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling
        )
        ui_scale_menu.set("100%")
        ui_scale_menu.pack(anchor="w", padx=20, pady=10)
        
        # Data management
        data_frame = ctk.CTkFrame(self.settings_frame)
        data_frame.pack(fill="x", padx=10, pady=10)
        
        data_label = ctk.CTkLabel(
            data_frame, 
            text="Data Management", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        data_label.pack(anchor="w", padx=10, pady=10)
        
        export_button = ctk.CTkButton(
            data_frame,
            text="Export Account Data",
            command=self.export_data
        )
        export_button.pack(anchor="w", padx=20, pady=10)
        
        clear_button = ctk.CTkButton(
            data_frame,
            text="Clear Account Data",
            command=self.clear_data,
            fg_color="red",
            hover_color="darkred"
        )
        clear_button.pack(anchor="w", padx=20, pady=10)
        
    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        
    def change_scaling(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        
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
            self.account_info.accounts = {"accounts": [], "statistics": {"success": 0, "failed": 0}}
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