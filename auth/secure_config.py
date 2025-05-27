"""
Secure Configuration Manager for n0name Trading Bot
Handles encrypted storage and secure management of sensitive configuration data.
"""

import os
import json
import secrets
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
import getpass
from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity


@dataclass
class SecureConfigData:
    """Secure configuration data structure"""
    # API credentials
    api_key: str = ""
    api_secret: str = ""
    
    # Telegram configuration
    telegram_token: str = ""
    telegram_chat_id: str = ""
    
    # Database credentials
    db_username: str = ""
    db_password: str = ""
    
    # Web UI credentials
    web_admin_username: str = "admin"
    web_admin_password: str = ""
    
    # JWT secret
    jwt_secret: str = ""
    
    # Encryption keys
    session_secret: str = ""
    
    # Additional secure fields
    webhook_secret: str = ""
    backup_encryption_key: str = ""


class SecureConfigManager:
    """Secure configuration manager with encryption"""
    
    def __init__(self, config_file: str = "secure_config.enc", master_key_file: str = "master.key"):
        self.config_file = Path(config_file)
        self.master_key_file = Path(master_key_file)
        self.logger = get_logger("secure_config")
        self._master_key: Optional[bytes] = None
        self._config_data: Optional[SecureConfigData] = None
        
        # Encryption parameters
        self.salt_size = 32
        self.nonce_size = 12
        self.tag_size = 16
        self.key_iterations = 200000  # Increased for better security
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        return PBKDF2(
            password.encode('utf-8'),
            salt,
            dkLen=32,  # 256-bit key
            count=self.key_iterations,
            hmac_hash_module=SHA256
        )
    
    def _generate_master_key(self) -> bytes:
        """Generate a new master key"""
        return get_random_bytes(32)
    
    def _encrypt_data(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data using AES-256-GCM"""
        nonce = get_random_bytes(self.nonce_size)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        
        # Return: nonce + tag + ciphertext
        return nonce + tag + ciphertext
    
    def _decrypt_data(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt data using AES-256-GCM"""
        nonce = encrypted_data[:self.nonce_size]
        tag = encrypted_data[self.nonce_size:self.nonce_size + self.tag_size]
        ciphertext = encrypted_data[self.nonce_size + self.tag_size:]
        
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)
    
    def initialize_secure_config(self, force_recreate: bool = False) -> bool:
        """Initialize secure configuration"""
        try:
            if self.config_file.exists() and not force_recreate:
                self.logger.info("Secure configuration already exists")
                return True
            
            print("\n🔐 Initializing Secure Configuration for n0name Trading Bot")
            print("=" * 60)
            
            # Get master password
            while True:
                password = getpass.getpass("Enter master password for configuration encryption: ")
                confirm_password = getpass.getpass("Confirm master password: ")
                
                if password == confirm_password:
                    if len(password) < 12:
                        print("❌ Password must be at least 12 characters long")
                        continue
                    break
                else:
                    print("❌ Passwords do not match")
            
            # Generate salt and derive key
            salt = get_random_bytes(self.salt_size)
            master_key = self._derive_key(password, salt)
            
            # Create default configuration
            config_data = SecureConfigData()
            
            # Collect sensitive data
            print("\n📝 Please provide the following sensitive information:")
            
            # API credentials
            config_data.api_key = input("Binance API Key: ").strip()
            config_data.api_secret = getpass.getpass("Binance API Secret: ").strip()
            
            # Telegram configuration
            config_data.telegram_token = input("Telegram Bot Token (optional): ").strip()
            if config_data.telegram_token:
                config_data.telegram_chat_id = input("Telegram Chat ID: ").strip()
            
            # Web UI admin password
            while True:
                web_password = getpass.getpass("Web UI Admin Password: ")
                if len(web_password) >= 8:
                    config_data.web_admin_password = web_password
                    break
                else:
                    print("❌ Web UI password must be at least 8 characters long")
            
            # Generate secure secrets
            config_data.jwt_secret = secrets.token_urlsafe(32)
            config_data.session_secret = secrets.token_urlsafe(32)
            config_data.webhook_secret = secrets.token_urlsafe(16)
            config_data.backup_encryption_key = secrets.token_urlsafe(32)
            
            # Serialize and encrypt configuration
            config_json = json.dumps(asdict(config_data), indent=2)
            encrypted_config = self._encrypt_data(config_json.encode('utf-8'), master_key)
            
            # Save encrypted configuration
            with open(self.config_file, 'wb') as f:
                f.write(salt + encrypted_config)
            
            # Set secure file permissions
            os.chmod(self.config_file, 0o600)
            
            self.logger.audit("Secure configuration initialized")
            print(f"✅ Secure configuration saved to {self.config_file}")
            print("🔒 File permissions set to 600 (owner read/write only)")
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to initialize secure configuration: {e}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.CRITICAL
            )
            return False
    
    def load_secure_config(self, password: Optional[str] = None) -> Optional[SecureConfigData]:
        """Load and decrypt secure configuration"""
        try:
            if not self.config_file.exists():
                self.logger.warning("Secure configuration file not found")
                return None
            
            # Get password if not provided
            if password is None:
                password = getpass.getpass("Enter master password: ")
            
            # Read encrypted file
            with open(self.config_file, 'rb') as f:
                file_data = f.read()
            
            if len(file_data) < self.salt_size:
                self.logger.error("Invalid secure configuration file format")
                return None
            
            # Extract salt and encrypted data
            salt = file_data[:self.salt_size]
            encrypted_data = file_data[self.salt_size:]
            
            # Derive key and decrypt
            master_key = self._derive_key(password, salt)
            decrypted_data = self._decrypt_data(encrypted_data, master_key)
            
            # Parse configuration
            config_dict = json.loads(decrypted_data.decode('utf-8'))
            self._config_data = SecureConfigData(**config_dict)
            
            self.logger.audit("Secure configuration loaded successfully")
            return self._config_data
            
        except Exception as e:
            self.logger.error(
                f"Failed to load secure configuration: {e}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.HIGH
            )
            return None
    
    def update_secure_config(self, updates: Dict[str, Any], password: Optional[str] = None) -> bool:
        """Update secure configuration"""
        try:
            # Load current configuration
            if self._config_data is None:
                current_config = self.load_secure_config(password)
                if current_config is None:
                    return False
            else:
                current_config = self._config_data
            
            # Apply updates
            config_dict = asdict(current_config)
            config_dict.update(updates)
            updated_config = SecureConfigData(**config_dict)
            
            # Save updated configuration
            return self.save_secure_config(updated_config, password)
            
        except Exception as e:
            self.logger.error(
                f"Failed to update secure configuration: {e}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.HIGH
            )
            return False
    
    def save_secure_config(self, config_data: SecureConfigData, password: Optional[str] = None) -> bool:
        """Save secure configuration"""
        try:
            if password is None:
                password = getpass.getpass("Enter master password: ")
            
            # Generate new salt for each save
            salt = get_random_bytes(self.salt_size)
            master_key = self._derive_key(password, salt)
            
            # Serialize and encrypt
            config_json = json.dumps(asdict(config_data), indent=2)
            encrypted_config = self._encrypt_data(config_json.encode('utf-8'), master_key)
            
            # Create backup of existing file
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.bak')
                self.config_file.rename(backup_file)
            
            # Save new configuration
            with open(self.config_file, 'wb') as f:
                f.write(salt + encrypted_config)
            
            # Set secure permissions
            os.chmod(self.config_file, 0o600)
            
            self._config_data = config_data
            self.logger.audit("Secure configuration saved")
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to save secure configuration: {e}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.HIGH
            )
            return False
    
    def get_api_credentials(self) -> Optional[Dict[str, str]]:
        """Get API credentials"""
        if self._config_data is None:
            return None
        
        return {
            'api_key': self._config_data.api_key,
            'api_secret': self._config_data.api_secret
        }
    
    def get_telegram_config(self) -> Optional[Dict[str, str]]:
        """Get Telegram configuration"""
        if self._config_data is None:
            return None
        
        return {
            'token': self._config_data.telegram_token,
            'chat_id': self._config_data.telegram_chat_id
        }
    
    def get_web_credentials(self) -> Optional[Dict[str, str]]:
        """Get web UI credentials"""
        if self._config_data is None:
            return None
        
        return {
            'username': self._config_data.web_admin_username,
            'password': self._config_data.web_admin_password
        }
    
    def get_jwt_secret(self) -> Optional[str]:
        """Get JWT secret"""
        if self._config_data is None:
            return None
        return self._config_data.jwt_secret
    
    def get_session_secret(self) -> Optional[str]:
        """Get session secret"""
        if self._config_data is None:
            return None
        return self._config_data.session_secret
    
    def rotate_secrets(self, password: Optional[str] = None) -> bool:
        """Rotate all secrets"""
        try:
            if self._config_data is None:
                current_config = self.load_secure_config(password)
                if current_config is None:
                    return False
            else:
                current_config = self._config_data
            
            # Generate new secrets
            current_config.jwt_secret = secrets.token_urlsafe(32)
            current_config.session_secret = secrets.token_urlsafe(32)
            current_config.webhook_secret = secrets.token_urlsafe(16)
            current_config.backup_encryption_key = secrets.token_urlsafe(32)
            
            # Save updated configuration
            success = self.save_secure_config(current_config, password)
            
            if success:
                self.logger.audit("Security secrets rotated")
                print("✅ All security secrets have been rotated")
            
            return success
            
        except Exception as e:
            self.logger.error(
                f"Failed to rotate secrets: {e}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.HIGH
            )
            return False
    
    def export_backup(self, backup_file: str, password: Optional[str] = None) -> bool:
        """Export encrypted backup of configuration"""
        try:
            if self._config_data is None:
                current_config = self.load_secure_config(password)
                if current_config is None:
                    return False
            else:
                current_config = self._config_data
            
            # Create backup with timestamp
            backup_data = {
                'timestamp': str(datetime.utcnow()),
                'version': '1.0',
                'config': asdict(current_config)
            }
            
            # Encrypt backup
            backup_json = json.dumps(backup_data, indent=2)
            backup_key = get_random_bytes(32)
            encrypted_backup = self._encrypt_data(backup_json.encode('utf-8'), backup_key)
            
            # Save backup
            backup_path = Path(backup_file)
            with open(backup_path, 'wb') as f:
                f.write(encrypted_backup)
            
            # Save backup key separately
            key_file = backup_path.with_suffix('.key')
            with open(key_file, 'wb') as f:
                f.write(base64.b64encode(backup_key))
            
            os.chmod(backup_path, 0o600)
            os.chmod(key_file, 0o600)
            
            self.logger.audit(f"Configuration backup exported to {backup_file}")
            print(f"✅ Backup exported to {backup_file}")
            print(f"🔑 Backup key saved to {key_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to export backup: {e}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.HIGH
            )
            return False
    
    def verify_integrity(self) -> bool:
        """Verify configuration file integrity"""
        try:
            if not self.config_file.exists():
                return False
            
            # Try to load configuration
            test_config = self.load_secure_config()
            return test_config is not None
            
        except Exception as e:
            self.logger.error(
                f"Configuration integrity check failed: {e}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.HIGH
            )
            return False


# Global secure config manager instance
_secure_config_manager: Optional[SecureConfigManager] = None


def get_secure_config_manager() -> SecureConfigManager:
    """Get global secure configuration manager"""
    global _secure_config_manager
    if _secure_config_manager is None:
        _secure_config_manager = SecureConfigManager()
    return _secure_config_manager


def initialize_secure_config() -> bool:
    """Initialize secure configuration"""
    manager = get_secure_config_manager()
    return manager.initialize_secure_config()


def load_secure_config() -> Optional[SecureConfigData]:
    """Load secure configuration"""
    manager = get_secure_config_manager()
    return manager.load_secure_config() 