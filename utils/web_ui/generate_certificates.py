#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for local development.
This script creates certificates that allow HTTPS on localhost.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

def generate_certificates():
    """Generate self-signed SSL certificates for localhost using Python cryptography library."""
    
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        print("❌ cryptography library not found. Installing...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            print("✅ cryptography library installed successfully!")
        except Exception as e:
            print(f"❌ Failed to install cryptography library: {e}")
            print("💡 Please install manually: pip install cryptography")
            return False
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    cert_dir = script_dir / "project" / "certs"
    
    # Create certificates directory
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / "localhost-cert.pem"
    key_file = cert_dir / "localhost-key.pem"
    
    # Check if certificates already exist
    if cert_file.exists() and key_file.exists():
        print("✅ SSL certificates already exist.")
        return True
    
    print("🔐 Generating SSL certificates for localhost...")
    
    try:
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print("✅ SSL certificates generated successfully!")
        print(f"📁 Certificate location: {cert_dir}")
        print(f"🔑 Private key: {key_file}")
        print(f"📜 Certificate: {cert_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating certificates: {e}")
        return False

def main():
    """Main function."""
    print("🚀 n0name Trading Dashboard - SSL Certificate Generator")
    print("=" * 60)
    
    success = generate_certificates()
    
    if success:
        print("\n🎉 Setup complete! You can now run the application with HTTPS support.")
        print("📝 Note: Your browser may show a security warning for self-signed certificates.")
        print("   This is normal for local development. Click 'Advanced' and 'Proceed to localhost'.")
    else:
        print("\n⚠️  Certificate generation failed. The application will fall back to HTTP.")
    
    return 0 if success else 1

if __name__ == "__main__":
    import ipaddress
    sys.exit(main()) 