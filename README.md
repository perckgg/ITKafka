# ITKafka

# IT Asset Management
This tool have two part:
- Agent (as Main Server) : responsible for collecting data from Collector
- Collector (as Client) : scan Computer and push data to Agent

# Collector Application
The Collector application is designed to gather system information from a machine and send it periodically to an Agent server (We can set up time directly in collector.py). This application can be packaged into an executable file using PyInstaller and can be run on any machine where Python is not installed.
## Table of content
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Building the Executable](#building-the-executable)
- [Running the Application](#running-the-application)
- [Troubleshooting](#troubleshooting)
## Features
- Collects system information like BIOS, disk details, and more.
- Sends the collected data to an Agent server at regular intervals.
- Configurable Agent IP address.
- Runs as a background process without showing a terminal window.
## Requirements
- Python 3.x
- pip (Python package manager)
- PyInstaller (for building the executable)
- Required Python packages:
  - Flask
  - requests
  - Flask-CORS

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/collector.git
cd collector
```
### 2. Install the Required Packages
Install the necessary Python packages using pip:
```bash
# 1. Create and activate virtualenv
$ python -m venv virtualenv
$ virtualenv\Scripts\activate (Windows)

# 2. Install dependencies
$ pip install -r requirements.txt
```

### 3. Configure the Collector
Before building or running the application, ensure that you have set the correct IP address of the Agent server in the collector.py file:
```bash
collector = Collector(agent_ip="192.168.1.100")  # Replace with the actual IP address of your Agent server
```
## Building the Executable
To distribute the application as an executable, you can use PyInstaller. However, if we scale larger (about 100+ computers), we will need to install it as .MSI file. 
### 1. Install PyInstaller
```bash
pip install pyinstaller
```
### 2. Build the Executable
```bash
pyinstaller --noconsole --onefile --icon=youricon.ico collector.py
```
## Installation
### Windows
Simply double-click the collector.exe file located in the dist folder. The application will start running in the background, collecting and sending data to the configured Agent server.
### Terminal/Command Line (Optional)
You can also run the application via the command line:
```bash
./collector.exe
```
## Running the Application
Run the collector.py file when need to test.
```bash
py collector.py
```
The app will run on port 7000.
Paste the below link on your browser:
```bash
localhost:7000/api/getData
```
After running collector -> Open another terminal and change folder to agent-service.
Finally run the command :
```bash
py newagent.py
```
or (not recommend to run)
```bash
py service.py
```
Then paste this link on the Web Browser:
```bash
localhost:5000
```
The data from collector will be displayed on the Browser, the information will be refreshed periodically.
## Troubleshooting
- Terminal Window Appears: Ensure you have used the --noconsole option in the PyInstaller command.
- Icon Not Displaying Correctly: Make sure your icon file is a properly formatted .ico file with multiple resolutions (16x16, 32x32, 48x48, 64x64, 128x128, 256x256).
- Connection Issues: Verify that the Agent server is running and reachable at the IP address specified in the Collector configuration.
