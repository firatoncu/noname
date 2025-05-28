"""
Async InfluxDB client for optimized database operations.

This module provides:
- Async InfluxDB initialization and management
- Connection pooling for database operations
- Batch writing capabilities
- Retry mechanisms for database operations
"""

import asyncio
import aiohttp
import aiofiles
import zipfile
import os
import sys
import subprocess
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import atexit
from datetime import datetime

from .async_utils import (
    AsyncHTTPClient, RetryConfig, RetryStrategy,
    get_http_client, async_cache
)

logger = logging.getLogger(__name__)


@dataclass
class InfluxDBConfig:
    """Configuration for InfluxDB client."""
    host: str = "localhost"
    port: int = 8086
    database: str = "n0namedb"
    username: Optional[str] = None
    password: Optional[str] = None
    ssl: bool = False
    verify_ssl: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    batch_size: int = 1000
    flush_interval: float = 1.0


class AsyncInfluxDBClient:
    """Async InfluxDB client with connection pooling and batching."""
    
    def __init__(self, config: InfluxDBConfig = None):
        self.config = config or InfluxDBConfig()
        self._http_client: Optional[AsyncHTTPClient] = None
        self._base_url = f"{'https' if self.config.ssl else 'http'}://{self.config.host}:{self.config.port}"
        self._auth = None
        self._batch_points: List[Dict[str, Any]] = []
        self._batch_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._closed = False
        
        if self.config.username and self.config.password:
            self._auth = aiohttp.BasicAuth(self.config.username, self.config.password)
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self):
        """Initialize connection to InfluxDB."""
        if self._http_client is None:
            self._http_client = get_http_client()
        
        # Test connection
        await self._test_connection()
        
        # Create database if it doesn't exist
        await self.create_database_if_not_exists()
        
        # Start batch flushing task
        self._start_batch_flushing()
        
        logger.info(f"Connected to InfluxDB at {self._base_url}")
    
    async def close(self):
        """Close the InfluxDB client."""
        if self._closed:
            return
        
        self._closed = True
        
        # Flush remaining batch points
        await self._flush_batch()
        
        # Cancel flush task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        logger.info("InfluxDB client closed")
    
    async def _test_connection(self):
        """Test connection to InfluxDB."""
        retry_config = RetryConfig(
            max_retries=self.config.max_retries,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        
        url = f"{self._base_url}/ping"
        
        try:
            async with self._http_client.get(
                url,
                auth=self._auth,
                retry_config=retry_config
            ) as response:
                if response.status == 204:
                    logger.info("InfluxDB connection test successful")
                else:
                    raise Exception(f"InfluxDB ping failed with status {response.status}")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise
    
    @async_cache(ttl_seconds=300)
    async def get_databases(self) -> List[str]:
        """Get list of databases."""
        url = f"{self._base_url}/query"
        params = {"q": "SHOW DATABASES"}
        
        async with self._http_client.get(
            url,
            params=params,
            auth=self._auth
        ) as response:
            if response.status == 200:
                data = await response.json()
                if "results" in data and data["results"]:
                    series = data["results"][0].get("series", [])
                    if series and "values" in series[0]:
                        return [db[0] for db in series[0]["values"]]
            return []
    
    async def create_database_if_not_exists(self):
        """Create database if it doesn't exist."""
        databases = await self.get_databases()
        
        if self.config.database not in databases:
            logger.info(f"Creating database '{self.config.database}'")
            await self.create_database(self.config.database)
        else:
            logger.info(f"Database '{self.config.database}' already exists")
    
    async def create_database(self, database_name: str):
        """Create a database."""
        url = f"{self._base_url}/query"
        params = {"q": f"CREATE DATABASE {database_name}"}
        
        async with self._http_client.post(
            url,
            params=params,
            auth=self._auth
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to create database: {error_text}")
    
    async def write_points(
        self,
        points: List[Dict[str, Any]],
        batch: bool = True
    ):
        """Write points to InfluxDB."""
        if batch:
            async with self._batch_lock:
                self._batch_points.extend(points)
                
                # Flush if batch is full
                if len(self._batch_points) >= self.config.batch_size:
                    await self._flush_batch()
        else:
            await self._write_points_direct(points)
    
    async def write_point(
        self,
        measurement: str,
        fields: Dict[str, Any],
        tags: Dict[str, str] = None,
        timestamp: datetime = None,
        batch: bool = True
    ):
        """Write a single point to InfluxDB."""
        point = {
            "measurement": measurement,
            "fields": fields,
            "tags": tags or {},
            "time": timestamp or datetime.utcnow()
        }
        
        await self.write_points([point], batch=batch)
    
    async def _write_points_direct(self, points: List[Dict[str, Any]]):
        """Write points directly to InfluxDB."""
        if not points:
            return
        
        # Convert points to line protocol
        lines = []
        for point in points:
            line = self._point_to_line_protocol(point)
            lines.append(line)
        
        data = "\n".join(lines)
        
        url = f"{self._base_url}/write"
        params = {"db": self.config.database}
        
        retry_config = RetryConfig(
            max_retries=self.config.max_retries,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        
        try:
            async with self._http_client.post(
                url,
                params=params,
                data=data,
                auth=self._auth,
                retry_config=retry_config,
                headers={"Content-Type": "application/octet-stream"}
            ) as response:
                if response.status not in (200, 204):
                    error_text = await response.text()
                    raise Exception(f"Failed to write points: {error_text}")
                
                logger.debug(f"Successfully wrote {len(points)} points to InfluxDB")
                
        except Exception as e:
            logger.error(f"Error writing points to InfluxDB: {e}")
            raise
    
    def _point_to_line_protocol(self, point: Dict[str, Any]) -> str:
        """Convert point to InfluxDB line protocol."""
        measurement = point["measurement"]
        
        # Build tags
        tag_parts = []
        if point.get("tags"):
            for key, value in point["tags"].items():
                tag_parts.append(f"{key}={value}")
        
        # Build fields
        field_parts = []
        for key, value in point["fields"].items():
            if isinstance(value, str):
                field_parts.append(f'{key}="{value}"')
            elif isinstance(value, bool):
                field_parts.append(f"{key}={str(value).lower()}")
            elif isinstance(value, int):
                field_parts.append(f"{key}={value}i")
            else:
                field_parts.append(f"{key}={value}")
        
        # Build line
        line_parts = [measurement]
        
        if tag_parts:
            line_parts[0] += "," + ",".join(tag_parts)
        
        line_parts.append(" " + ",".join(field_parts))
        
        # Add timestamp
        if point.get("time"):
            timestamp = point["time"]
            if isinstance(timestamp, datetime):
                timestamp = int(timestamp.timestamp() * 1_000_000_000)  # nanoseconds
            line_parts.append(f" {timestamp}")
        
        return "".join(line_parts)
    
    async def query(
        self,
        query: str,
        database: str = None,
        epoch: str = None
    ) -> Dict[str, Any]:
        """Execute a query against InfluxDB."""
        url = f"{self._base_url}/query"
        params = {
            "q": query,
            "db": database or self.config.database
        }
        
        if epoch:
            params["epoch"] = epoch
        
        retry_config = RetryConfig(
            max_retries=self.config.max_retries,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        
        async with self._http_client.get(
            url,
            params=params,
            auth=self._auth,
            retry_config=retry_config
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Query failed: {error_text}")
    
    async def _flush_batch(self):
        """Flush batched points to InfluxDB."""
        if not self._batch_points:
            return
        
        points_to_write = self._batch_points.copy()
        self._batch_points.clear()
        
        try:
            await self._write_points_direct(points_to_write)
        except Exception as e:
            logger.error(f"Error flushing batch: {e}")
            # Re-add points to batch for retry
            async with self._batch_lock:
                self._batch_points.extend(points_to_write)
    
    def _start_batch_flushing(self):
        """Start background task for batch flushing."""
        async def flush_worker():
            while not self._closed:
                try:
                    await asyncio.sleep(self.config.flush_interval)
                    async with self._batch_lock:
                        if self._batch_points:
                            await self._flush_batch()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in batch flush worker: {e}")
        
        self._flush_task = asyncio.create_task(flush_worker())


class AsyncInfluxDBManager:
    """Manager for InfluxDB server and client operations."""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or self._get_base_path()
        self._influxd_process: Optional[subprocess.Popen] = None
        self._client: Optional[AsyncInfluxDBClient] = None
    
    def _get_base_path(self) -> str:
        """Get base path for InfluxDB installation."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.dirname(os.path.dirname(current_dir))
    
    async def download_and_extract_influxdb(self) -> str:
        """Download and extract InfluxDB if not found."""
        url = 'https://dl.influxdata.com/influxdb/releases/influxdb-1.8.10_windows_amd64.zip'
        archive_name = os.path.join(self.base_path, 'influxdb.zip')
        extract_dir = os.path.join(self.base_path, 'influxdb-1.8.10-1')
        binary_path = os.path.join(extract_dir, 'influxd.exe')
        
        # Check if binary already exists
        if os.path.exists(binary_path):
            logger.info(f"InfluxDB binary already exists at {binary_path}")
            return binary_path
        
        logger.info(f"Downloading InfluxDB from {url}")
        
        # Download using async HTTP client
        http_client = get_http_client()
        
        try:
            async with http_client.get(url) as response:
                if response.status == 200:
                    # Write file asynchronously
                    async with aiofiles.open(archive_name, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                else:
                    raise Exception(f"Download failed with status {response.status}")
            
            logger.info(f"Extracting InfluxDB to {self.base_path}")
            
            # Extract archive (this is CPU-bound, so we run it in executor)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._extract_archive,
                archive_name,
                self.base_path
            )
            
            # Clean up archive
            os.remove(archive_name)
            
            return binary_path
            
        except Exception as e:
            logger.error(f"Error downloading/extracting InfluxDB: {e}")
            raise
    
    def _extract_archive(self, archive_path: str, extract_path: str):
        """Extract archive (runs in executor)."""
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    
    async def start_influxdb_server(self, binary_path: str):
        """Start InfluxDB server process."""
        logger.info(f"Starting InfluxDB server from {binary_path}")
        
        # Start process in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        def start_process():
            CREATE_NO_WINDOW = 0x08000000
            return subprocess.Popen([binary_path], creationflags=CREATE_NO_WINDOW)
        
        self._influxd_process = await loop.run_in_executor(None, start_process)
        
        # Register cleanup on exit
        atexit.register(self._cleanup_process)
        
        # Wait for server to initialize
        await asyncio.sleep(10)
        
        logger.info("InfluxDB server started")
    
    def _cleanup_process(self):
        """Clean up InfluxDB process."""
        if self._influxd_process:
            self._influxd_process.terminate()
    
    async def get_client(self, config: InfluxDBConfig = None) -> AsyncInfluxDBClient:
        """Get InfluxDB client instance."""
        if self._client is None:
            self._client = AsyncInfluxDBClient(config)
            await self._client.connect()
        return self._client
    
    async def initialize(self, config: InfluxDBConfig = None) -> AsyncInfluxDBClient:
        """Initialize InfluxDB server and client."""
        try:
            # Download and extract InfluxDB if needed
            binary_path = await self.download_and_extract_influxdb()
            
            # Start InfluxDB server
            await self.start_influxdb_server(binary_path)
            
            # Create and connect client
            client = await self.get_client(config)
            
            logger.info("InfluxDB initialization complete")
            return client
            
        except Exception as e:
            logger.error(f"InfluxDB initialization failed: {e}")
            raise
    
    async def close(self):
        """Close InfluxDB manager."""
        if self._client:
            await self._client.close()
            self._client = None
        
        self._cleanup_process()


# Global manager instance
_influxdb_manager: Optional[AsyncInfluxDBManager] = None


def get_influxdb_manager() -> AsyncInfluxDBManager:
    """Get global InfluxDB manager instance."""
    global _influxdb_manager
    if _influxdb_manager is None:
        _influxdb_manager = AsyncInfluxDBManager()
    return _influxdb_manager


async def initialize_influxdb(config: InfluxDBConfig = None) -> AsyncInfluxDBClient:
    """Initialize InfluxDB and return client."""
    manager = get_influxdb_manager()
    return await manager.initialize(config)


async def cleanup_influxdb():
    """Clean up InfluxDB resources."""
    global _influxdb_manager
    if _influxdb_manager:
        await _influxdb_manager.close()
        _influxdb_manager = None 