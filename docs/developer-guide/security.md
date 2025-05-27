# API KEY Management

## User Input Collection

First, the user is prompted to enter their API Key, API Secret, and a secure password. The password is collected using `getpass`, which ensures it isn’t displayed on the screen, adding an initial layer of security.

## Generating Random Values

Next, the system generates two random values:

- A 16-byte salt, which helps make the encryption key unique even if the same password is used elsewhere.
- A 12-byte nonce, which ensures each encryption is unique, preventing potential security issues if the same data is encrypted multiple times.

## Key Derivation

The user’s password is then used with the salt to derive a 256-bit encryption key using PBKDF2. This process involves:

- **100,000 iterations** to slow down the key derivation, making it harder for attackers to guess the password.
- **SHA-256** as the hash function, which is a secure method for this purpose.

## Data Encryption

The API Key and API Secret are combined into one string with a colon (e.g., `API_KEY:API_SECRET`) and encrypted using AES-256-GCM. This method not only encrypts the data but also generates an authentication tag to verify the data hasn’t been tampered with.

## Storage

Finally, the salt, nonce, authentication tag, and encrypted data (ciphertext) are stored in a binary file named `encrypted_keys.bin`. The file is structured as follows:

- **First 16 bytes**: Salt
- **Next 12 bytes**: Nonce
- **Next 16 bytes**: Authentication tag
- **Remaining bytes**: Ciphertext

This ensures the keys are securely stored and can only be accessed with the correct password.

# Detailed Explanation

## Introduction to the Encryption Procedure

The encryption procedure aims to enhance the security of the Binance Futures trading robot by replacing plain-text storage of API keys with encrypted storage. This is critical to prevent unauthorized access, especially given the sensitivity of API credentials. The method uses AES-256-GCM for encryption and PBKDF2 for key derivation, both of which are industry-standard cryptographic techniques.

## Step-by-Step Encryption Process

### User Input Collection

- The user is prompted to provide the API Key, API Secret, and a secure password.
- The password is entered using `getpass`, which prevents the input from being echoed to the console, enhancing security during entry.

### Generation of Cryptographic Components

- A **random salt of 16 bytes** is generated using a secure random number generator like `os.urandom` in Python.
- A **random nonce of 12 bytes** is also generated. In AES-GCM, the nonce ensures unique ciphertexts for identical plaintexts.

### Key Derivation Using PBKDF2

The encryption key is derived from the user’s password using PBKDF2 with the following parameters:

- **Password**: The user-provided password, encoded as bytes.
- **Salt**: The 16-byte random salt generated earlier.
- **Iterations**: 100,000 to slow down brute-force attacks.
- **Hash function**: SHA-256 for secure key derivation.
- **Output**: A 256-bit (32-byte) key for AES-256-GCM encryption.

### Data Preparation for Encryption

- The API Key and API Secret are concatenated with a colon (e.g., `API_KEY:API_SECRET`) and encoded as bytes.
- The choice of a colon as a delimiter is simple, but other formats like JSON could also be considered for robustness.

### Encryption Using AES-256-GCM

- The concatenated string is encrypted using AES-256-GCM with the derived 256-bit key and the generated nonce.
- The output includes:
  - **Ciphertext**: The encrypted form of the concatenated string.
  - **Authentication tag**: A 16-byte value to ensure the ciphertext’s integrity.

### Storage in Binary File

The encrypted data and decryption components are stored in `encrypted_keys.bin`:

- **First 16 bytes**: Salt (for key derivation)
- **Next 12 bytes**: Nonce (for AES-GCM decryption)
- **Next 16 bytes**: Authentication tag (for integrity verification)
- **Remaining bytes**: Ciphertext (encrypted API keys)

# Additional Considerations

## Password Security

- Users should select strong, unique passwords.
- Consider using a password manager to securely store passwords.

## Password Recovery

- There is no password recovery mechanism. Losing the password results in losing access to the encrypted keys.

## File Integrity

- The binary file should be stored securely with proper permissions to prevent tampering.

## Performance Impact

- The 100,000 iterations in PBKDF2 add a minor delay, which improves security by slowing down brute-force attacks.

## Table: Encryption Components and Their Roles

| Component              |   Size    |                        Role                                      |
|------------------------|-----------|------------------------------------------------------------------|
| **Salt**               | 16 bytes  | Ensures unique key derivation, prevents rainbow table attacks.   |
| **Nonce**              | 12 bytes  | Ensures unique encryption, prevents nonce reuse vulnerabilities. |
| **Authentication Tag** | 16 bytes  | Verifies integrity and authenticity of ciphertext.               |
| **Ciphertext**         | Variable  | Encrypted form of the API Key and API Secret.                    |


This encryption approach ensures API keys are securely stored and can only be decrypted with the correct password, significantly enhancing security compared to plain-text storage

# Security Policy

## Reporting a Vulnerability

We take the security of the **n0name** trading bot seriously and welcome contributions from the community to help identify and address potential vulnerabilities. If you discover a security issue, please follow the steps below to report it responsibly.

### How to Report
To report a vulnerability, please include the following details in your report to help us understand and address the issue efficiently:
- A clear description of the vulnerability, including the affected component or functionality.
- Steps to reproduce the issue, if applicable.
- Any potential impact you foresee (e.g., data exposure, unauthorized access, or trading disruptions).
- Your contact information for follow-up communication.


### Response Timeline
Once you submit a vulnerability report:
- **Acknowledgment**: You can expect an initial acknowledgment of your report within **48 hours** of submission.
- **Updates**: We will provide periodic updates on the status of your report approximately every **7-14 days**, depending on the complexity of the issue.
- **Resolution**: We aim to resolve critical vulnerabilities within **30 days** of confirmation, though timelines may vary based on the nature and scope of the issue.

### What to Expect
- **If Accepted**: If we confirm the vulnerability, we will work to develop and deploy a fix as quickly as possible. You will be credited for your discovery (unless you prefer to remain anonymous) in our release notes or acknowledgments section, and we may reach out for additional input during the resolution process.
- **If Declined**: If the reported issue is determined to be a non-vulnerability (e.g., intended behavior, out of scope, or unexploitable), we will provide a detailed explanation of our reasoning. You’re welcome to follow up if you have additional evidence or questions.

### Scope
This vulnerability reporting process applies to the core **n0name** trading bot codebase and its direct dependencies. Issues related to third-party services (e.g., Binance API) or user misconfiguration are generally out of scope, though we’re happy to assist with troubleshooting where possible.

### Responsible Disclosure
We kindly request that you refrain from publicly disclosing the vulnerability until we’ve had a reasonable opportunity to investigate and address it. This helps protect our users and maintain the integrity of the project.
