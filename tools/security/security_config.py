# Security Configuration for n0name Trading Bot
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
