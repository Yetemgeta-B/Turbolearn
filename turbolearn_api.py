import os
import json
import time
import random
import threading
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from turbolearn_signup import TurboLearnSignup

# Initialize Flask app
app = Flask(__name__, static_folder='web/static', template_folder='web/templates')
CORS(app)  # Enable cross-origin requests for mobile clients
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', str(uuid.uuid4()))

# Storage for automation sessions and results
active_sessions = {}
account_database = []
proxy_list = []
user_credentials = {"admin": generate_password_hash("turbolearn123")}

# Paths for data storage
DATA_DIR = os.path.join(os.path.expanduser("~"), "turbolearn_data")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
PROXIES_FILE = os.path.join(DATA_DIR, "proxies.json")
CREDENTIALS_FILE = os.path.join(DATA_DIR, "credentials.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Load existing data
def load_data():
    global account_database, proxy_list, user_credentials
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r') as f:
                account_database = json.load(f)
        if os.path.exists(PROXIES_FILE):
            with open(PROXIES_FILE, 'r') as f:
                proxy_list = json.load(f)
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                user_credentials = json.load(f)
    except Exception as e:
        print(f"Error loading data: {str(e)}")

# Save data to disk
def save_data():
    try:
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(account_database, f)
        with open(PROXIES_FILE, 'w') as f:
            json.dump(proxy_list, f)
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(user_credentials, f)
    except Exception as e:
        print(f"Error saving data: {str(e)}")

# Authentication function
def authenticate(username, password):
    if username in user_credentials:
        return check_password_hash(user_credentials[username], password)
    return False

# Generate a unique browser fingerprint
def generate_fingerprint():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    
    fingerprint = {
        "user_agent": random.choice(user_agents),
        "screen_resolution": random.choice(["1920x1080", "1366x768", "2560x1440", "1440x900"]),
        "color_depth": random.choice([24, 32]),
        "timezone_offset": random.randint(-12, 12),
        "language": random.choice(["en-US", "en-GB", "es-ES", "fr-FR", "de-DE"]),
        "session_id": str(uuid.uuid4())
    }
    
    return fingerprint

# Function to run automation with error recovery
def run_automation_session(session_id, params):
    try:
        # Update session status
        active_sessions[session_id]["status"] = "running"
        active_sessions[session_id]["progress"] = 0
        active_sessions[session_id]["logs"] = []
        
        # Add log messages
        def add_log(message, level="info"):
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            log_entry = {"timestamp": timestamp, "message": message, "level": level}
            active_sessions[session_id]["logs"].append(log_entry)
        
        add_log("Starting automation session", "info")
        
        # Set up proxy if provided
        proxy = None
        if "proxy" in params and params["proxy"]:
            proxy = params["proxy"]
            add_log(f"Using proxy: {proxy}", "info")
        elif proxy_list and params.get("use_random_proxy", False):
            proxy = random.choice(proxy_list)
            add_log(f"Using random proxy: {proxy}", "info")
        
        # Set up browser fingerprint
        fingerprint = None
        if params.get("use_fingerprinting", False):
            fingerprint = generate_fingerprint()
            add_log("Using custom browser fingerprint", "info")
        
        # Initialize the signup process
        browser = params.get("browser", "chrome")
        headless = params.get("headless", False)
        
        # Multi-browser support
        instance_count = params.get("instances", 1)
        accounts = []
        threads = []
        
        def browser_instance(instance_id):
            try:
                # Create a unique instance name
                instance_name = f"instance_{instance_id}"
                add_log(f"Starting browser instance {instance_id}", "info")
                
                # Initialize TurboLearnSignup
                signup = TurboLearnSignup(
                    browser=browser,
                    headless=headless,
                    proxy=proxy,
                    fingerprint=fingerprint
                )
                
                # Run the signup process
                account = signup.create_account()
                accounts.append(account)
                
                # Update progress
                progress = (instance_id / instance_count) * 100
                active_sessions[session_id]["progress"] = progress
                
                add_log(f"Account creation successful for instance {instance_id}", "success")
                add_log(f"Email: {account['email']}", "info")
                add_log(f"Password: {account['password']}", "info")
                
            except Exception as e:
                add_log(f"Error in instance {instance_id}: {str(e)}", "error")
                
                # AI-powered error recovery attempt
                if params.get("enable_error_recovery", False):
                    add_log("Attempting error recovery...", "info")
                    try:
                        # Implement error recovery logic here
                        # For now, we'll just retry once with a different approach
                        signup = TurboLearnSignup(
                            browser=browser,
                            headless=True,  # Force headless mode
                            proxy=proxy
                        )
                        account = signup.create_account()
                        accounts.append(account)
                        add_log("Error recovery successful", "success")
                    except Exception as recovery_error:
                        add_log(f"Error recovery failed: {str(recovery_error)}", "error")
        
        # Start multiple browser instances if configured
        for i in range(instance_count):
            if instance_count > 1:
                # Use threading for parallel execution
                thread = threading.Thread(target=browser_instance, args=(i+1,))
                threads.append(thread)
                thread.start()
                # Small delay to prevent overloading
                time.sleep(2)
            else:
                # Single instance, run directly
                browser_instance(1)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Save accounts to database
        for account in accounts:
            if account not in account_database:
                account_database.append(account)
        save_data()
        
        # Update session status
        active_sessions[session_id]["status"] = "completed"
        active_sessions[session_id]["progress"] = 100
        active_sessions[session_id]["result"] = accounts
        active_sessions[session_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        # Handle exceptions at the session level
        active_sessions[session_id]["status"] = "failed"
        active_sessions[session_id]["error"] = str(e)
        
        # Add error log
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        log_entry = {"timestamp": timestamp, "message": f"Session failed: {str(e)}", "level": "error"}
        active_sessions[session_id]["logs"].append(log_entry)

# API Routes

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    """API endpoint for user authentication"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if authenticate(username, password):
        token = str(uuid.uuid4())
        return jsonify({"success": True, "token": token})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/start_automation', methods=['POST'])
def start_automation():
    """API endpoint to start an automation session"""
    # Authentication check would go here in production
    
    data = request.json
    session_id = str(uuid.uuid4())
    
    active_sessions[session_id] = {
        "id": session_id,
        "params": data,
        "status": "initializing",
        "created_at": datetime.now().isoformat(),
        "progress": 0,
        "logs": []
    }
    
    # Start the automation in a background thread
    thread = threading.Thread(target=run_automation_session, args=(session_id, data))
    thread.start()
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "message": "Automation session started"
    })

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """API endpoint to get status of an automation session"""
    if session_id in active_sessions:
        return jsonify({
            "success": True,
            "session": active_sessions[session_id]
        })
    else:
        return jsonify({
            "success": False,
            "message": "Session not found"
        }), 404

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """API endpoint to list all automation sessions"""
    return jsonify({
        "success": True,
        "sessions": list(active_sessions.values())
    })

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """API endpoint to get all created accounts"""
    return jsonify({
        "success": True,
        "accounts": account_database
    })

@app.route('/api/proxies', methods=['GET'])
def get_proxies():
    """API endpoint to get all available proxies"""
    return jsonify({
        "success": True,
        "proxies": proxy_list
    })

@app.route('/api/proxies', methods=['POST'])
def add_proxy():
    """API endpoint to add a new proxy"""
    data = request.json
    proxy = data.get('proxy')
    
    if proxy and proxy not in proxy_list:
        proxy_list.append(proxy)
        save_data()
        return jsonify({
            "success": True,
            "message": "Proxy added successfully"
        })
    else:
        return jsonify({
            "success": False,
            "message": "Invalid proxy or proxy already exists"
        }), 400

@app.route('/api/users', methods=['POST'])
def create_user():
    """API endpoint to create a new user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username and password and username not in user_credentials:
        user_credentials[username] = generate_password_hash(password)
        save_data()
        return jsonify({
            "success": True,
            "message": "User created successfully"
        })
    else:
        return jsonify({
            "success": False,
            "message": "Invalid username/password or user already exists"
        }), 400

# Load data at startup
load_data()

# Run the API server when executed directly
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 