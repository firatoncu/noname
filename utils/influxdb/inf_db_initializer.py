import os
import sys
import subprocess
import requests
import zipfile
import time
import atexit
from influxdb import InfluxDBClient

# Determine the base path (works for both script and PyInstaller executable)
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # Running as Python script
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    BASE_PATH = os.path.dirname(BASE_PATH)
    BASE_PATH = os.path.dirname(BASE_PATH)

def download_and_extract_influxdb(base_path):
    print("\nInf DB Init")
    """Download and extract InfluxDB 1.8.10 to the executable path if not found."""
    url = 'https://dl.influxdata.com/influxdb/releases/influxdb-1.8.10_windows_amd64.zip'
    archive_name = os.path.join(base_path, 'influxdb.zip')
    extract_dir = os.path.join(base_path, 'influxdb-1.8.10-1')
    binary_path = os.path.join(extract_dir, 'influxd.exe')

    # Check if InfluxDB binary already exists in the executable path
    if os.path.exists(binary_path):
        print(f"InfluxDB binary already exists at {binary_path}")
        return binary_path

    # Download the archive to the executable path
    print(f"InfluxDB not found. Downloading from {url} to {base_path}...")
    response = requests.get(url)
    with open(archive_name, 'wb') as f:
        f.write(response.content)

    # Extract the archive to the executable path
    print(f"Extracting InfluxDB archive to {base_path}...")
    with zipfile.ZipFile(archive_name, 'r') as zip_ref:
        zip_ref.extractall(base_path)

    # Clean up the downloaded zip file (optional)
    os.remove(archive_name)

    return binary_path

def start_influxdb(binary_path):
    """Start the InfluxDB server process from the given path."""
    print(f"Starting InfluxDB server from {binary_path}...")
    # Run influxd.exe in the background; suppress console window with CREATE_NO_WINDOW
    CREATE_NO_WINDOW = 0x08000000
    influxd_process = subprocess.Popen([binary_path], creationflags=CREATE_NO_WINDOW)
    time.sleep(10)  # Wait for the server to initialize
    return influxd_process

def create_database_if_not_exists(client, db_name='n0name-db'):
    """Check if the database exists; create it if not found."""
    print(f"Checking if database '{db_name}' exists...")
    # Get list of existing databases
    databases = client.get_list_database()
    db_exists = any(db['name'] == db_name for db in databases)
    
    if db_exists:
        print(f"Database '{db_name}' already exists.")
    else:
        print(f"Database '{db_name}' not found. Creating it...")
        client.create_database(db_name)
    
    # Switch to the database
    client.switch_database(db_name)
    return client

def inf_db_init_main():
    # Use the executable/script base path
    global BASE_PATH
    
    # Download and extract InfluxDB if not found in the executable path
    binary_path = download_and_extract_influxdb(BASE_PATH)
    
    # Start the InfluxDB server
    influxd_process = start_influxdb(binary_path)
    # Ensure the server shuts down when the script exits
    atexit.register(lambda: influxd_process.terminate())
    
    # Connect to InfluxDB and create database if it doesn't exist
    print("Connecting to InfluxDB...")
    client = InfluxDBClient(host='localhost', port=8086)
    client = create_database_if_not_exists(client, 'n0name-db')
