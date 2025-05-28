#!/usr/bin/env python3
"""
Security Setup Script for n0name Trading Bot
Initializes secure configuration, generates certificates, and sets up security measures.
"""

import os
import sys
import argparse
import getpass
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auth.secure_config import SecureConfigManager, initialize_secure_config
from auth.security_manager import SecurityManager, SecurityConfig
from utils.web_ui.generate_certificates import generate_certificates
from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity


class SecuritySetup:
    """Security setup and configuration manager"""
    
    def __init__(self):
        self.logger = get_logger("security_setup")
        self.secure_config = SecureConfigManager()
        
    def print_banner(self):
        """Print setup banner"""
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        n0name Trading Bot Security Setup                     ║
║                                                                              ║
║  This script will help you set up comprehensive security for your trading   ║
║  bot, including encrypted configuration, SSL certificates, and secure       ║
║  authentication.                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        # Map package names to their import names
        package_imports = {
            'cryptography': 'cryptography',
            'passlib': 'passlib',
            'bcrypt': 'bcrypt',
            'PyJWT': 'jwt',
            'fastapi': 'fastapi',
            'uvicorn': 'uvicorn'
        }
        
        missing_packages = []
        
        for package, import_name in package_imports.items():
            try:
                __import__(import_name)
                print(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"  ❌ {package}")
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("Please install them using:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
        
        print("✅ All dependencies are installed!")
        return True
    
    def setup_secure_config(self, force_recreate=False):
        """Set up secure configuration"""
        print("\n🔐 Setting up secure configuration...")
        
        if self.secure_config.config_file.exists() and not force_recreate:
            print("Secure configuration already exists.")
            response = input("Do you want to recreate it? (y/N): ").lower()
            if response != 'y':
                return True
        
        success = self.secure_config.initialize_secure_config(force_recreate)
        
        if success:
            print("✅ Secure configuration created successfully!")
            return True
        else:
            print("❌ Failed to create secure configuration!")
            return False
    
    def setup_ssl_certificates(self):
        """Set up SSL certificates"""
        print("\n🔒 Setting up SSL certificates...")
        
        cert_dir = project_root / "utils" / "web_ui" / "project" / "certs"
        cert_file = cert_dir / "localhost-cert.pem"
        key_file = cert_dir / "localhost-key.pem"
        
        if cert_file.exists() and key_file.exists():
            print("SSL certificates already exist.")
            response = input("Do you want to regenerate them? (y/N): ").lower()
            if response != 'y':
                return True
        
        success = generate_certificates()
        
        if success:
            print("✅ SSL certificates generated successfully!")
            return True
        else:
            print("❌ Failed to generate SSL certificates!")
            return False
    
    def setup_file_permissions(self):
        """Set up secure file permissions"""
        print("\n🔧 Setting up file permissions...")
        
        # Files that should have restricted permissions
        secure_files = [
            "secure_config.enc",
            "encrypted_keys.bin",
            "utils/web_ui/project/certs/localhost-key.pem",
            "utils/web_ui/project/certs/localhost-cert.pem"
        ]
        
        for file_path in secure_files:
            full_path = project_root / file_path
            if full_path.exists():
                try:
                    os.chmod(full_path, 0o600)  # Owner read/write only
                    print(f"  ✅ {file_path} - permissions set to 600")
                except Exception as e:
                    print(f"  ⚠️  {file_path} - failed to set permissions: {e}")
            else:
                print(f"  ⏭️  {file_path} - file not found, skipping")
        
        print("✅ File permissions configured!")
        return True
    
    def create_security_config_file(self):
        """Create security configuration file"""
        print("\n⚙️  Creating security configuration...")
        
        config_content = """# Security Configuration for n0name Trading Bot
# This file contains security settings and should be reviewed carefully

# Session Configuration
SESSION_TIMEOUT = 7200  # 2 hours
MAX_SESSIONS_PER_USER = 3
SESSION_CLEANUP_INTERVAL = 300  # 5 minutes

# Authentication Configuration
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_UPPERCASE = True
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes

# Rate Limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # 1 minute

# Security Headers
ENABLE_SECURITY_HEADERS = True
ENABLE_CSRF_PROTECTION = True

# IP Restrictions (modify as needed)
ALLOWED_IP_RANGES = [
    "127.0.0.1/32",
    "::1/128",
    # "192.168.0.0/16",  # Uncomment for local network access
    # "10.0.0.0/8",      # Uncomment for private network access
]

BLOCKED_IPS = [
    # Add IP addresses to block here
]

# Logging
SECURITY_LOG_LEVEL = "INFO"
AUDIT_LOG_ENABLED = True

# Production Settings
# Set these to True in production environment
PRODUCTION_MODE = False
REQUIRE_HTTPS = False
STRICT_TRANSPORT_SECURITY = False
"""
        
        config_file = project_root / "security_config.py"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            os.chmod(config_file, 0o644)  # Read-only for group/others
            print(f"✅ Security configuration created: {config_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create security configuration: {e}")
            return False
    
    def create_startup_script(self):
        """Create secure startup script"""
        print("\n📝 Creating secure startup script...")
        
        startup_content = """#!/usr/bin/env python3
\"\"\"
Secure startup script for n0name Trading Bot
Uses the secure API with authentication and encryption.
\"\"\"

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auth.secure_config import get_secure_config_manager
from utils.web_ui.project.api.secure_main import start_secure_server_and_updater
from utils.enhanced_logging import get_logger
from binance import AsyncClient

async def main():
    logger = get_logger("secure_startup")
    
    try:
        # Load secure configuration
        secure_config = get_secure_config_manager()
        config_data = secure_config.load_secure_config()
        
        if not config_data:
            print("❌ Failed to load secure configuration!")
            print("Please run: python setup_security.py --setup-config")
            return
        
        # Get API credentials
        api_creds = secure_config.get_api_credentials()
        if not api_creds:
            print("❌ No API credentials found in secure configuration!")
            return
        
        # Initialize Binance client
        client = await AsyncClient.create(
            api_creds['api_key'],
            api_creds['api_secret']
        )
        
        # Define trading symbols (modify as needed)
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
        
        logger.info("Starting secure trading bot...")
        
        # Start secure server and updater
        server_task, updater_task = await start_secure_server_and_updater(symbols, client)
        
        # Wait for tasks to complete
        await asyncio.gather(server_task, updater_task)
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Startup error: {e}")
    finally:
        if 'client' in locals():
            await client.close_connection()

if __name__ == "__main__":
    asyncio.run(main())
"""
        
        startup_file = project_root / "start_secure.py"
        
        try:
            with open(startup_file, 'w', encoding='utf-8') as f:
                f.write(startup_content)
            
            os.chmod(startup_file, 0o755)  # Executable
            print(f"✅ Secure startup script created: {startup_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create startup script: {e}")
            return False
    
    def create_requirements_security(self):
        """Create security requirements file"""
        print("\n📦 Creating security requirements...")
        
        security_requirements = """# Security-related dependencies for n0name Trading Bot
cryptography>=41.0.0
passlib[bcrypt]>=1.7.4
PyJWT>=2.8.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
bcrypt>=4.0.1
argon2-cffi>=23.1.0

# Web security
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6

# Additional security tools
pyotp>=2.9.0  # For 2FA support
qrcode>=7.4.2  # For 2FA QR codes
"""
        
        req_file = project_root / "requirements-security.txt"
        
        try:
            with open(req_file, 'w', encoding='utf-8') as f:
                f.write(security_requirements)
            
            print(f"✅ Security requirements created: {req_file}")
            print("Install with: pip install -r requirements-security.txt")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create security requirements: {e}")
            return False
    
    def verify_setup(self):
        """Verify security setup"""
        print("\n🔍 Verifying security setup...")
        
        checks = [
            ("Secure configuration file", self.secure_config.config_file.exists()),
            ("SSL certificate", (project_root / "utils/web_ui/project/certs/localhost-cert.pem").exists()),
            ("SSL private key", (project_root / "utils/web_ui/project/certs/localhost-key.pem").exists()),
            ("Security config", (project_root / "security_config.py").exists()),
            ("Startup script", (project_root / "start_secure.py").exists()),
        ]
        
        all_passed = True
        
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 Security setup completed successfully!")
            print("\nNext steps:")
            print("1. Review and modify security_config.py as needed")
            print("2. Install security requirements: pip install -r requirements-security.txt")
            print("3. Start the secure bot: python start_secure.py")
            print("4. Access the web interface at: https://localhost:8000")
            print("5. Default login: admin / admin123!@# (CHANGE IN PRODUCTION!)")
        else:
            print("\n⚠️  Some security setup checks failed. Please review and fix the issues.")
        
        return all_passed
    
    def run_full_setup(self, force_recreate=False):
        """Run full security setup"""
        self.print_banner()
        
        if not self.check_dependencies():
            return False
        
        steps = [
            ("Setting up secure configuration", lambda: self.setup_secure_config(force_recreate)),
            ("Setting up SSL certificates", self.setup_ssl_certificates),
            ("Setting up file permissions", self.setup_file_permissions),
            ("Creating security config", self.create_security_config_file),
            ("Creating startup script", self.create_startup_script),
            ("Creating security requirements", self.create_requirements_security),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Failed: {step_name}")
                return False
        
        return self.verify_setup()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="n0name Trading Bot Security Setup")
    parser.add_argument("--setup-config", action="store_true", help="Setup secure configuration only")
    parser.add_argument("--setup-certs", action="store_true", help="Setup SSL certificates only")
    parser.add_argument("--verify", action="store_true", help="Verify security setup")
    parser.add_argument("--force", action="store_true", help="Force recreate existing files")
    parser.add_argument("--full", action="store_true", help="Run full security setup")
    
    args = parser.parse_args()
    
    setup = SecuritySetup()
    
    if args.setup_config:
        setup.setup_secure_config(args.force)
    elif args.setup_certs:
        setup.setup_ssl_certificates()
    elif args.verify:
        setup.verify_setup()
    elif args.full or len(sys.argv) == 1:
        setup.run_full_setup(args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 