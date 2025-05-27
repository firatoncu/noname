"""
Configuration models using Pydantic for type safety and validation.

This module defines all configuration models used throughout the application,
providing comprehensive validation and type safety.
"""

from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
from pathlib import Path
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.networks import AnyUrl
from enum import Enum

from ..types import (
    Symbol,
    Price,
    Quantity,
    Percentage,
    Leverage,
    APIKey,
    APISecret,
    DatabaseURL,
    FilePath,
    TimeInterval,
)


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ExchangeType(str, Enum):
    """Supported exchange types."""
    BINANCE = "binance"
    BINANCE_FUTURES = "binance_futures"
    BINANCE_US = "binance_us"


class DatabaseType(str, Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    INFLUXDB = "influxdb"


class CacheType(str, Enum):
    """Supported cache types."""
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"


class NotificationType(str, Enum):
    """Supported notification types."""
    EMAIL = "email"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    WEBHOOK = "webhook"


class StrategyType(str, Enum):
    """Supported strategy types."""
    BOLLINGER_RSI = "bollinger_rsi"
    MACD_FIBONACCI = "macd_fibonacci"
    CUSTOM = "custom"


class ExchangeConfig(BaseModel):
    """Exchange configuration."""
    
    type: ExchangeType = ExchangeType.BINANCE
    api_key: APIKey
    api_secret: APISecret
    testnet: bool = False
    sandbox: bool = False
    rate_limit: int = Field(default=1200, ge=1, le=10000)
    timeout: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=1, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    
    class Config:
        use_enum_values = True


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    type: DatabaseType = DatabaseType.SQLITE
    url: Optional[DatabaseURL] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    pool_recycle: int = Field(default=3600, ge=300, le=86400)
    echo: bool = False
    
    @root_validator
    def validate_database_config(cls, values):
        """Validate database configuration."""
        db_type = values.get('type')
        url = values.get('url')
        host = values.get('host')
        
        if not url and not host:
            if db_type == DatabaseType.SQLITE:
                values['url'] = "sqlite:///data/trading_bot.db"
            else:
                raise ValueError("Either 'url' or 'host' must be provided for non-SQLite databases")
        
        return values
    
    class Config:
        use_enum_values = True


class CacheConfig(BaseModel):
    """Cache configuration."""
    
    type: CacheType = CacheType.MEMORY
    host: Optional[str] = None
    port: Optional[int] = None
    password: Optional[str] = None
    database: int = Field(default=0, ge=0, le=15)
    max_connections: int = Field(default=10, ge=1, le=100)
    timeout: int = Field(default=5, ge=1, le=60)
    default_ttl: int = Field(default=3600, ge=60, le=86400)  # 1 hour default
    
    class Config:
        use_enum_values = True


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[FilePath] = None
    max_file_size: int = Field(default=10485760, ge=1048576)  # 10MB default
    backup_count: int = Field(default=5, ge=1, le=50)
    console_output: bool = True
    structured_logging: bool = True
    log_to_database: bool = False
    
    class Config:
        use_enum_values = True


class RiskConfig(BaseModel):
    """Risk management configuration."""
    
    max_position_size: Percentage = Field(default=0.1, ge=0.01, le=1.0)  # 10% of capital
    max_daily_loss: Percentage = Field(default=0.05, ge=0.01, le=0.5)  # 5% daily loss limit
    max_drawdown: Percentage = Field(default=0.2, ge=0.05, le=0.8)  # 20% max drawdown
    risk_per_trade: Percentage = Field(default=0.02, ge=0.005, le=0.1)  # 2% risk per trade
    max_open_positions: int = Field(default=5, ge=1, le=50)
    stop_loss_percentage: Percentage = Field(default=0.02, ge=0.005, le=0.1)  # 2% stop loss
    take_profit_ratio: float = Field(default=2.0, ge=1.0, le=10.0)  # 2:1 risk/reward
    position_sizing_method: str = Field(default="fixed_percentage", regex="^(fixed_percentage|kelly|volatility_adjusted)$")
    
    @validator('max_daily_loss')
    def validate_daily_loss(cls, v, values):
        """Ensure daily loss is less than max drawdown."""
        max_drawdown = values.get('max_drawdown', 0.2)
        if v >= max_drawdown:
            raise ValueError('max_daily_loss must be less than max_drawdown')
        return v


class StrategyConfig(BaseModel):
    """Strategy configuration."""
    
    name: str
    type: StrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    symbols: List[Symbol] = Field(default_factory=list)
    timeframe: TimeInterval = "5m"
    lookback_period: int = Field(default=500, ge=50, le=5000)
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate trading symbols."""
        if not v:
            raise ValueError('At least one symbol must be specified')
        return [symbol.upper() for symbol in v]
    
    class Config:
        use_enum_values = True


class TradingConfig(BaseModel):
    """Main trading configuration."""
    
    capital: Decimal = Field(default=Decimal("10000"), gt=0)
    leverage: Leverage = Field(default=1, ge=1, le=125)
    symbols: List[Symbol] = Field(default_factory=list)
    strategy: StrategyConfig
    risk: RiskConfig = Field(default_factory=RiskConfig)
    auto_start: bool = False
    paper_trading: bool = True
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate and normalize trading symbols."""
        if not v:
            raise ValueError('At least one trading symbol must be specified')
        return [symbol.upper() for symbol in v]


class NotificationConfig(BaseModel):
    """Notification configuration."""
    
    enabled: bool = True
    types: List[NotificationType] = Field(default_factory=lambda: [NotificationType.EMAIL])
    email: Optional[Dict[str, str]] = None
    telegram: Optional[Dict[str, str]] = None
    discord: Optional[Dict[str, str]] = None
    slack: Optional[Dict[str, str]] = None
    webhook: Optional[Dict[str, str]] = None
    
    @root_validator
    def validate_notification_configs(cls, values):
        """Validate notification type configurations."""
        enabled = values.get('enabled', True)
        types = values.get('types', [])
        
        if enabled and types:
            for notification_type in types:
                config_key = notification_type.value
                if not values.get(config_key):
                    raise ValueError(f'Configuration for {notification_type} is required when enabled')
        
        return values
    
    class Config:
        use_enum_values = True


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    
    enabled: bool = True
    metrics_collection: bool = True
    performance_tracking: bool = True
    health_checks: bool = True
    alert_thresholds: Dict[str, float] = Field(default_factory=dict)
    dashboard_port: int = Field(default=8080, ge=1024, le=65535)
    metrics_retention_days: int = Field(default=30, ge=1, le=365)
    
    @validator('alert_thresholds')
    def validate_thresholds(cls, v):
        """Validate alert thresholds."""
        valid_metrics = {
            'cpu_usage', 'memory_usage', 'error_rate', 'latency',
            'position_count', 'daily_pnl', 'drawdown'
        }
        
        for metric in v.keys():
            if metric not in valid_metrics:
                raise ValueError(f'Unknown metric: {metric}')
        
        return v


class SecurityConfig(BaseModel):
    """Security configuration."""
    
    encryption_enabled: bool = True
    api_key_encryption: bool = True
    database_encryption: bool = False
    ssl_verify: bool = True
    rate_limiting: bool = True
    ip_whitelist: List[str] = Field(default_factory=list)
    session_timeout: int = Field(default=3600, ge=300, le=86400)  # 1 hour default
    max_login_attempts: int = Field(default=5, ge=1, le=20)
    
    @validator('ip_whitelist')
    def validate_ip_addresses(cls, v):
        """Validate IP addresses in whitelist."""
        import ipaddress
        
        for ip in v:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                try:
                    ipaddress.ip_network(ip, strict=False)
                except ValueError:
                    raise ValueError(f'Invalid IP address or network: {ip}')
        
        return v


class WebUIConfig(BaseModel):
    """Web UI configuration."""
    
    enabled: bool = True
    host: str = "localhost"
    port: int = Field(default=3000, ge=1024, le=65535)
    debug: bool = False
    auto_reload: bool = True
    cors_enabled: bool = True
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    
    @validator('cors_origins')
    def validate_cors_origins(cls, v):
        """Validate CORS origins."""
        for origin in v:
            if not origin.startswith(('http://', 'https://')):
                raise ValueError(f'Invalid CORS origin: {origin}')
        return v


class BacktestConfig(BaseModel):
    """Backtesting configuration."""
    
    enabled: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: Decimal = Field(default=Decimal("10000"), gt=0)
    commission: Percentage = Field(default=0.001, ge=0, le=0.1)  # 0.1% commission
    slippage: Percentage = Field(default=0.0005, ge=0, le=0.01)  # 0.05% slippage
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        """Validate date format."""
        if v:
            from datetime import datetime
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v


class AppConfig(BaseModel):
    """Main application configuration."""
    
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    version: str = "2.0.0"
    
    # Core configurations
    trading: TradingConfig
    exchange: ExchangeConfig
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Optional configurations
    notifications: Optional[NotificationConfig] = None
    monitoring: Optional[MonitoringConfig] = None
    web_ui: Optional[WebUIConfig] = None
    backtest: Optional[BacktestConfig] = None
    
    # Additional settings
    data_directory: FilePath = Field(default="data")
    log_directory: FilePath = Field(default="logs")
    config_directory: FilePath = Field(default="config")
    
    @root_validator
    def validate_directories(cls, values):
        """Ensure required directories exist."""
        directories = ['data_directory', 'log_directory', 'config_directory']
        
        for dir_key in directories:
            dir_path = values.get(dir_key)
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        return values
    
    @validator('environment')
    def validate_environment_settings(cls, v, values):
        """Validate environment-specific settings."""
        if v == Environment.PRODUCTION:
            # Ensure production safety
            if values.get('debug', False):
                raise ValueError('Debug mode cannot be enabled in production')
            
            trading_config = values.get('trading')
            if trading_config and trading_config.paper_trading:
                raise ValueError('Paper trading should be disabled in production')
        
        return v
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"  # Prevent additional fields 