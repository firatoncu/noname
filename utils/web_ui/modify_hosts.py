import os
import sys

def is_admin():
    try:
        return os.getuid() == 0  # For Unix-like systems
    except AttributeError:
        # For Windows
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def add_to_hosts(hostname, ip="127.0.0.1"):
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    new_entry = f"{ip} {hostname}"
    
    # Check if running as admin
    if not is_admin():
        print("Please run as administrator")
        return False
    
    try:
        # Verify file exists
        if not os.path.exists(hosts_path):
            print("Hosts file not found!")
            return False
            
        # Read existing content
        with open(hosts_path, 'r') as file:
            content = file.readlines()
            
        # Remove trailing whitespace and empty lines for checking
        content = [line.strip() for line in content]
        
        # Check if entry already exists
        if new_entry.strip() in content:
            return True
            
        # Append new entry
        with open(hosts_path, 'a') as file:
            file.write(f"\n{new_entry}\n")
            
        print(f"Successfully added '{new_entry}' to hosts file")
        return True
        
    except PermissionError:
        print("Permission denied: Please run as administrator")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False