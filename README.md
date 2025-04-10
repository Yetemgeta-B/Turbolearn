# 🚀 TurboLearn Crack

[![Python 3.6+](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Selenium](https://img.shields.io/badge/Selenium-4.12.0-green.svg)](https://www.selenium.dev/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Visitors](https://visitor-badge.laobi.icu/badge?page_id=turbolearn-crack)](https://github.com/your-username/TurboLearnCrack)

This tool automates the process of creating an account on TurboLearn.ai using Selenium for browser automation with an intuitive GUI interface.

![TurboLearn GUI](https://img.shields.io/badge/GUI-CustomTkinter-blue)

## ✨ Features

- 🖥️ **User-friendly GUI** with modern CustomTkinter interface
- 🔍 **Auto-detects browsers** installed on your system
- 🌐 Supports **multiple browsers**: Chrome, Firefox, Edge, Vivaldi, Brave, and Opera
- 🕵️ **Private browsing mode** option for enhanced privacy
- 🤖 **Headless mode** for faster, invisible automation
- 📊 **Dashboard** to track and manage created accounts
- 🔄 Copy account information with one click
- 🚀 Open accounts directly in your browser
- 📈 **Analytics** with visualizations of account creation success rates
- 📅 **Scheduler** for automated account creation at specified times
- 🔄 **Batch processing** to create multiple accounts in sequence
- 🌍 **Proxy support** for location-based testing
- 💼 **WebDriver management** with included drivers for Chrome, Firefox, and Edge
- 🛡️ **Error handling** with real-time console output
- 🎨 **Themes and UI scaling** options
- 🔐 **Password management** with secure storage
- 🔗 **Desktop shortcut creation** with custom application icon

## 🛠️ Requirements

- Python 3.6+
- At least one of the supported browsers installed:
  - Google Chrome
  - Mozilla Firefox
  - Microsoft Edge
  - Vivaldi
  - Brave
  - Opera
- Internet connection

## 📥 Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Additional packages for enhanced features:
   - `pywin32` and `winshell` for Windows desktop shortcut creation
   - `pillow` for icon generation

## 🚀 Usage

Run the GUI application with:

```bash
python turbolearn_gui.py
```

Or run the CLI version with:

```bash
python turbolearn_signup.py
```

### 🖱️ GUI Features

The application provides several tabs:

- **Automation**: Control the account creation process with various options
- **Dashboard**: View and manage created accounts
  - Toggle dashboard login for privacy
  - Copy account details and open accounts in your browser
- **Analytics**: Visualize account creation success rates
- **Scheduler**: Set up automated account creation tasks
- **Settings**: Configure application appearance and manage data
  - Change appearance mode (Light/Dark)
  - Adjust UI scaling
  - Toggle dashboard login
  - Create desktop shortcut
  - Change password

### ⌨️ Command-line options (CLI version)

- `--private`: Start the browser in private/incognito mode
- `--browser NAME`: Specify browser to use (chrome, firefox, edge, vivaldi, brave, opera)
- `--driver PATH`: Specify a custom WebDriver executable path
- `--clear-cache`: Clear WebDriver cache before starting (fixes many WebDriver errors)
- `--manual-driver`: Force manual download of the WebDriver instead of using the automatic manager

Examples:
```bash
# Run with private browsing
python turbolearn_signup.py --private

# Specify browser to use
python turbolearn_signup.py --browser firefox

# Use a specific WebDriver executable
python turbolearn_signup.py --driver C:\path\to\chromedriver.exe

# Clear the WebDriver cache to fix errors
python turbolearn_signup.py --clear-cache
```

## 🎨 Customization

The application now features:
- A blue color scheme (#3a7ebf) for a professional look
- Custom application icon that matches the color scheme
- Responsive and clean user interface

## ⚠️ Note

This tool is for educational purposes only. Please respect TurboLearn's terms of service and policies.

## 🔧 Troubleshooting

- If the script fails to find elements on the page, it might be because the website structure has changed. Update the XPath selectors as needed.
- If a browser is not detected automatically but you know it's installed, you can specify it in the GUI or with the `--browser` option in CLI.
- If you experience WebDriver compatibility issues:
  1. Use the built-in WebDrivers in the `drivers` directory
  2. Try using the `--clear-cache` option in CLI mode
  3. Download a compatible WebDriver manually and select it in the GUI
  4. Make sure your browser is up to date
  5. Try a different browser
- For desktop shortcut creation issues:
  1. Make sure `pywin32` and `winshell` are installed (`pip install pywin32 winshell`)
  2. For icon generation, ensure `pillow` is installed (`pip install pillow`)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📜 License

MIT License

## GitHub Releases

TurboLearn Crack provides an easy way to create and distribute executable releases:

1. Run the packaging script:
   ```
   python package_release.py
   ```

2. This will:
   - Create a standalone executable using PyInstaller
   - Package it with necessary files into a 'release' folder
   - Provide instructions on uploading to GitHub Releases

3. To publish the release on GitHub:
   - Go to your GitHub repository
   - Click on 'Releases' in the right sidebar
   - Click 'Create a new release'
   - Fill in the tag version (e.g., v1.0.0)
   - Add a release title and description
   - Upload the files from the 'release' directory
   - Click 'Publish release'

Users can then download and run the standalone executable without needing to install Python or dependencies. 