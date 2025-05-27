"""
Comprehensive Security Manager for n0name Trading Bot
Handles authentication, session management, input validation, and security headers.
"""

import os
import secrets
import hashlib
import hmac
import time
import re
import html
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import ipaddress
from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity


class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuthenticationMethod(Enum):
    """Supported authentication methods"""
    PASSWORD = "password"
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    TWO_FACTOR = "2fa"


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    # Session settings
    session_timeout: int = 3600  # 1 hour
    max_sessions_per_user: int = 3
    session_cleanup_interval: int = 300  # 5 minutes
    
    # Authentication settings
    password_min_length: int = 12
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    
    # JWT settings
    jwt_secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # 1 minute
    
    # Input validation
    max_input_length: int = 1000
    allowed_symbols_pattern: str = r'^[A-Z0-9]+USDT$'
    
    # Security headers
    enable_security_headers: bool = True
    enable_csrf_protection: bool = True
    
    # IP restrictions
    allowed_ip_ranges: List[str] = field(default_factory=lambda: ['127.0.0.1/32', '::1/128'])
    blocked_ips: List[str] = field(default_factory=list)


@dataclass
class UserSession:
    """User session data"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    permissions: List[str] = field(default_factory=list)


@dataclass
class SecurityEvent:
    """Security event for audit logging"""
    event_type: str
    user_id: Optional[str]
    ip_address: str
    timestamp: datetime
    details: Dict[str, Any]
    severity: SecurityLevel


class InputValidator:
    """Input validation and sanitization"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = get_logger("security.input_validator")
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate trading symbol format"""
        if not symbol or len(symbol) > 20:
            return False
        return bool(re.match(self.config.allowed_symbols_pattern, symbol))
    
    def validate_numeric_input(self, value: Any, min_val: float = 0, max_val: float = float('inf')) -> bool:
        """Validate numeric input"""
        try:
            num_val = float(value)
            return min_val <= num_val <= max_val
        except (ValueError, TypeError):
            return False
    
    def sanitize_string(self, input_str: str) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return ""
        
        # Limit length
        if len(input_str) > self.config.max_input_length:
            input_str = input_str[:self.config.max_input_length]
        
        # HTML escape
        sanitized = html.escape(input_str)
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        return sanitized.strip()
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < self.config.password_min_length:
            errors.append(f"Password must be at least {self.config.password_min_length} characters long")
        
        if self.config.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.config.password_require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if self.config.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def validate_api_request(self, request_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate API request data"""
        errors = []
        
        # Check for required fields based on request type
        if 'symbol' in request_data:
            if not self.validate_symbol(request_data['symbol']):
                errors.append("Invalid symbol format")
        
        # Validate numeric fields
        numeric_fields = ['quantity', 'price', 'take_profit_percentage', 'stop_loss_percentage']
        for field in numeric_fields:
            if field in request_data:
                if not self.validate_numeric_input(request_data[field]):
                    errors.append(f"Invalid {field} value")
        
        return len(errors) == 0, errors


class SessionManager:
    """Session management for user authentication"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.sessions: Dict[str, UserSession] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        self.login_attempts: Dict[str, List[datetime]] = {}  # ip_address -> [attempt_times]
        self.logger = get_logger("security.session_manager")
        self._cleanup_task = None
    
    def start_cleanup_task(self):
        """Start the session cleanup task"""
        if self._cleanup_task is None:
            try:
                loop = asyncio.get_running_loop()
                self._cleanup_task = loop.create_task(self._cleanup_sessions())
            except RuntimeError:
                # No event loop running, cleanup task will be started later
                pass
    
    def stop_cleanup_task(self):
        """Stop the session cleanup task"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
    
    def create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        """Create a new user session"""
        # Check for too many sessions
        if user_id in self.user_sessions:
            if len(self.user_sessions[user_id]) >= self.config.max_sessions_per_user:
                # Remove oldest session
                oldest_session_id = self.user_sessions[user_id].pop(0)
                self.sessions.pop(oldest_session_id, None)
        
        # Generate secure session ID
        session_id = secrets.token_urlsafe(32)
        
        # Create session
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        self.logger.audit(
            f"Session created for user {user_id}",
            extra={
                "session_id": session_id,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
        )
        
        return session_id
    
    def validate_session(self, session_id: str, ip_address: str) -> Optional[UserSession]:
        """Validate and update session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session is active
        if not session.is_active:
            return None
        
        # Check session timeout
        if datetime.utcnow() - session.last_activity > timedelta(seconds=self.config.session_timeout):
            self.invalidate_session(session_id)
            return None
        
        # Check IP address consistency
        if session.ip_address != ip_address:
            self.logger.warning(
                f"IP address mismatch for session {session_id}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.HIGH,
                extra={
                    "original_ip": session.ip_address,
                    "current_ip": ip_address
                }
            )
            self.invalidate_session(session_id)
            return None
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        return session
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            
            # Remove from user sessions
            if session.user_id in self.user_sessions:
                if session_id in self.user_sessions[session.user_id]:
                    self.user_sessions[session.user_id].remove(session_id)
            
            self.logger.audit(f"Session invalidated: {session_id}")
    
    def check_login_attempts(self, identifier: str) -> bool:
        """Check if login attempts are within limits"""
        now = datetime.utcnow()
        
        if identifier not in self.login_attempts:
            self.login_attempts[identifier] = []
        
        # Remove old attempts
        self.login_attempts[identifier] = [
            attempt for attempt in self.login_attempts[identifier]
            if now - attempt < timedelta(seconds=self.config.lockout_duration)
        ]
        
        return len(self.login_attempts[identifier]) < self.config.max_login_attempts
    
    def record_login_attempt(self, identifier: str, success: bool):
        """Record a login attempt"""
        if not success:
            if identifier not in self.login_attempts:
                self.login_attempts[identifier] = []
            self.login_attempts[identifier].append(datetime.utcnow())
    
    async def _cleanup_sessions(self):
        """Periodic session cleanup"""
        while True:
            try:
                await asyncio.sleep(self.config.session_cleanup_interval)
                
                now = datetime.utcnow()
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    if (now - session.last_activity).total_seconds() > self.config.session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    self.invalidate_session(session_id)
                
                if expired_sessions:
                    self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                    
            except Exception as e:
                self.logger.error(f"Error in session cleanup: {e}")


class AuthenticationManager:
    """Authentication and authorization manager"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.session_manager = SessionManager(config)
        self.logger = get_logger("security.auth_manager")
        
        # Default admin user (should be changed in production)
        self.users = {
            "admin": {
                "password_hash": self.hash_password("admin123!@#"),
                "permissions": ["read", "write", "admin"],
                "is_active": True
            }
        }
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def authenticate_user(self, username: str, password: str, ip_address: str, user_agent: str) -> Optional[str]:
        """Authenticate user and create session"""
        # Check login attempts
        if not self.session_manager.check_login_attempts(ip_address):
            self.logger.warning(
                f"Too many login attempts from {ip_address}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.HIGH
            )
            return None
        
        # Validate user
        if username not in self.users:
            self.session_manager.record_login_attempt(ip_address, False)
            return None
        
        user = self.users[username]
        if not user["is_active"] or not self.verify_password(password, user["password_hash"]):
            self.session_manager.record_login_attempt(ip_address, False)
            return None
        
        # Create session
        session_id = self.session_manager.create_session(username, ip_address, user_agent)
        self.session_manager.record_login_attempt(ip_address, True)
        
        self.logger.audit(
            f"User {username} authenticated successfully",
            extra={"ip_address": ip_address}
        )
        
        return session_id
    
    def create_jwt_token(self, user_id: str, permissions: List[str]) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "permissions": permissions,
            "exp": datetime.utcnow() + timedelta(seconds=self.config.jwt_expiration),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for FastAPI"""
    
    def __init__(self, app, security_manager):
        super().__init__(app)
        self.security_manager = security_manager
        self.rate_limiter = {}
        self.logger = get_logger("security.middleware")
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware"""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # IP filtering
            if not self._check_ip_allowed(client_ip):
                self.logger.warning(
                    f"Blocked request from unauthorized IP: {client_ip}",
                    category=ErrorCategory.SECURITY,
                    severity=LogSeverity.HIGH
                )
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied"}
                )
            
            # Rate limiting
            if not self._check_rate_limit(client_ip):
                self.logger.warning(
                    f"Rate limit exceeded for IP: {client_ip}",
                    category=ErrorCategory.SECURITY,
                    severity=LogSeverity.MEDIUM
                )
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            # Log request
            process_time = time.time() - start_time
            self.logger.info(
                f"Request processed: {request.method} {request.url.path}",
                extra={
                    "ip_address": client_ip,
                    "user_agent": request.headers.get("user-agent", ""),
                    "process_time": process_time,
                    "status_code": response.status_code
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                f"Error in security middleware: {e}",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.HIGH,
                extra={"ip_address": client_ip}
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _check_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP address is allowed"""
        try:
            client_ip = ipaddress.ip_address(ip_address)
            
            # Check blocked IPs
            for blocked_ip in self.security_manager.config.blocked_ips:
                if client_ip in ipaddress.ip_network(blocked_ip, strict=False):
                    return False
            
            # Check allowed ranges
            for allowed_range in self.security_manager.config.allowed_ip_ranges:
                if client_ip in ipaddress.ip_network(allowed_range, strict=False):
                    return True
            
            return False
            
        except ValueError:
            return False
    
    def _check_rate_limit(self, ip_address: str) -> bool:
        """Check rate limiting"""
        now = time.time()
        window_start = now - self.security_manager.config.rate_limit_window
        
        if ip_address not in self.rate_limiter:
            self.rate_limiter[ip_address] = []
        
        # Remove old requests
        self.rate_limiter[ip_address] = [
            req_time for req_time in self.rate_limiter[ip_address]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.rate_limiter[ip_address]) >= self.security_manager.config.rate_limit_requests:
            return False
        
        # Add current request
        self.rate_limiter[ip_address].append(now)
        return True
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        if self.security_manager.config.enable_security_headers:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"


class SecurityManager:
    """Main security manager class"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.auth_manager = AuthenticationManager(self.config)
        self.input_validator = InputValidator(self.config)
        self.logger = get_logger("security.manager")
        
        # Security event log
        self.security_events: List[SecurityEvent] = []
    
    def get_middleware(self):
        """Get security middleware"""
        return SecurityMiddleware(None, self)
    
    def start_session_cleanup(self):
        """Start session cleanup task"""
        self.auth_manager.session_manager.start_cleanup_task()
    
    def stop_session_cleanup(self):
        """Stop session cleanup task"""
        self.auth_manager.session_manager.stop_cleanup_task()
    
    async def start_async_cleanup(self):
        """Start async cleanup task when event loop is running"""
        try:
            # Start the session cleanup task
            self.auth_manager.session_manager.start_cleanup_task()
            self.logger.info("Async session cleanup started")
        except Exception as e:
            self.logger.error(f"Failed to start async cleanup: {e}")
    
    async def stop_async_cleanup(self):
        """Stop async cleanup task"""
        try:
            self.auth_manager.session_manager.stop_cleanup_task()
            self.logger.info("Async session cleanup stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop async cleanup: {e}")
    
    def log_security_event(self, event_type: str, user_id: Optional[str], ip_address: str, details: Dict[str, Any], severity: SecurityLevel = SecurityLevel.MEDIUM):
        """Log security event"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            details=details,
            severity=severity
        )
        
        self.security_events.append(event)
        
        # Log to main logger
        self.logger.audit(
            f"Security event: {event_type}",
            category=ErrorCategory.SECURITY,
            severity=LogSeverity.HIGH if severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL] else LogSeverity.MEDIUM,
            extra={
                "user_id": user_id,
                "ip_address": ip_address,
                "details": details,
                "severity": severity.value
            }
        )
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        recent_events = [e for e in self.security_events if e.timestamp > last_24h]
        
        return {
            "total_events_24h": len(recent_events),
            "critical_events_24h": len([e for e in recent_events if e.severity == SecurityLevel.CRITICAL]),
            "high_events_24h": len([e for e in recent_events if e.severity == SecurityLevel.HIGH]),
            "active_sessions": len(self.auth_manager.session_manager.sessions),
            "blocked_ips": len(self.config.blocked_ips),
            "last_updated": now.isoformat()
        } 