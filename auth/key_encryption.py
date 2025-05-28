import os
import sys
import getpass
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from colorama import Fore, Style, init
import random
from time import sleep
from utils.enhanced_logging import get_logger

logger = get_logger()

init()



def encrypt_api_keys():
    try:
        sleep(1)
        print(
        """
        Welcome to the n0name API Key Encryption Setup.
        This is the Setup function to encrypt and store your API Key and API Secret.
        Prompts the user for credentials and a secure password, then:
        - Generates a random salt (16 bytes) and nonce (12 bytes)
        - Derives a 256-bit encryption key using PBKDF2 (with 100,000 iterations)
        - Encrypts the concatenated "API_KEY:API_SECRET" string with AES-256-GCM
        - Writes the salt, nonce, tag, and ciphertext to ENCRYPTED_FILE
        (long story short: it's super secure and you won't have to worry about storing your keys in plaintext.)
        """)
        ENCRYPTED_FILE = "encrypted_keys.bin"
        # Prompt user for credentials
        api_key = input("Enter your Binance API Key: ").strip()
        print(f"Enter your Binance API Secret: {Fore.LIGHTBLACK_EX}(you won't see it on screen when you paste it.){Style.RESET_ALL}")
        api_secret = getpass.getpass("Secret: ").strip()
        password = getpass.getpass("Enter a secure password for encryption: ").strip()

        # Generate random salt and nonce
        salt = get_random_bytes(16)         # 16-byte salt
        nonce = get_random_bytes(12)        # 12-byte nonce for AES-GCM

        # Derive a 256-bit encryption key from the password using PBKDF2
        key = PBKDF2(password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)

        # Prepare data and encrypt it using AES-256-GCM
        data = f"{api_key}:{api_secret}".encode('utf-8')
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(data)

        if getattr(sys, 'frozen', False):  # Running as PyInstaller executable
            base_path = os.path.dirname(sys.executable)
        else:  # Running as a Python script
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(base_path)

        ENCRYPTED_FILE = os.path.join(base_path, ENCRYPTED_FILE)

        # Write salt, nonce, tag, and ciphertext to the encrypted file
        with open(ENCRYPTED_FILE, "wb") as f:
            f.write(salt + nonce + tag + ciphertext)
        
        print(f"Encryption complete. Encrypted keys stored in '{ENCRYPTED_FILE}'.")
    
    except Exception as e:
        logger.error(f"Error while encryption: {e}")

def decrypt_api_keys():
    """
    Decrypts the API credentials stored in ENCRYPTED_FILE.
    Steps:
      - Verifies that the file exists
      - Reads salt (16 bytes), nonce (12 bytes), authentication tag (16 bytes), and ciphertext
      - Derives the encryption key using the same PBKDF2 parameters
      - Decrypts and verifies the data using AES-256-GCM
      - Splits the decrypted string to return the API Key and API Secret
    If decryption fails (e.g. wrong password or corrupted data), an error is shown.
    """
    try:
        # List of available foreground colors (excluding RESET)
        colors = [
            Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA,
            Fore.CYAN, Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
            Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX, Fore.WHITE
        ]
        ENCRYPTED_FILE = "encrypted_keys.bin"
        # Choose a random color
        random_color = random.choice(colors)
        os.system("cls" if os.name == "nt" else "clear") 
        print(f"""{random_color}{Style.BRIGHT}
                    _                             ______                         
                    (_)           _               / __   |                        
    ____   ____ ___  _  ____ ____| |_  _    ____ | | //| |____   ____ ____   ____ 
    |  _ \ / ___) _ \| |/ _  ) ___)  _)(_)  |  _ \| |// | |  _ \ / _  |    \ / _  )
    | | | | |  | |_| | ( (/ ( (___| |__ _   | | | |  /__| | | | ( ( | | | | ( (/ / 
    | ||_/|_|   \___/| |\____)____)\___|_)  |_| |_|\_____/|_| |_|\_||_|_|_|_|\____)
    |_|            (__/                                                            
    {Style.RESET_ALL}""")
        print(f"\n\n{Style.BRIGHT}Welcome to the project: n0name !\n\n  {Style.RESET_ALL}")
        print("This is the decryption function to securely retrieve your API Key and API Secret.")
        
        if getattr(sys, 'frozen', False):  # Running as PyInstaller executable
            base_path = os.path.dirname(sys.executable)
        else:  # Running as a Python script
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(base_path)
            
        ENCRYPTED_FILE = os.path.join(base_path, ENCRYPTED_FILE)

        if not os.path.exists(ENCRYPTED_FILE):
            input("\n\nEncrypted keys file not found. Press Enter to start the encryption process..")
            encrypt_api_keys()

        password = getpass.getpass("\n\n\nEnter the password to decrypt the API keys: ").strip()
        sleep(1)
        
        # Read and parse the encrypted file
        with open(ENCRYPTED_FILE, "rb") as f:
            file_content = f.read()

        if len(file_content) < (16 + 12 + 16):
            print("Invalid encrypted keys file.")
            sys.exit(1)

        salt = file_content[:16]
        nonce = file_content[16:28]
        tag = file_content[28:44]
        ciphertext = file_content[44:]

        # Derive the encryption key using PBKDF2 with the stored salt
        key = PBKDF2(password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        
        try:
            decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
        except Exception:
            print("\nIncorrect password or corrupted data.")
            sys.exit(1)
        
        # Decode the decrypted data and split to extract API Key and API Secret
        decrypted_str = decrypted_data.decode('utf-8')
        if ':' not in decrypted_str:
            print("\nDecrypted data format is invalid.")
            sys.exit(1)
        
        api_key, api_secret = decrypted_str.split(":", 1)
        return api_key, api_secret

    except Exception as e:
        logger.error(f"Error while decryption: {e}")