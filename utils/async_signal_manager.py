"""
Async Signal Manager for optimized signal processing.

This module provides:
- Async signal processing and management
- Non-blocking cleanup operations
- Async persistence with batching
- Concurrent signal validation
"""

import asyncio
import aiofiles
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import threading
from dataclasses import dataclass, field

from .signal_manager import (
    Signal, SignalType, SignalStatus, SignalHistory,
    SignalManager as BaseSignalManager
)
from .async_utils import get_task_manager, async_cache

logger = logging.getLogger(__name__)


class AsyncSignalManager(BaseSignalManager):
    """Async version of SignalManager with optimized operations."""
    
    def __init__(self, persistence_file: Optional[str] = None, auto_cleanup: bool = True):
        # Initialize base class without starting cleanup thread
        super().__init__(persistence_file, auto_cleanup=False)
        
        # Async-specific attributes
        self._async_lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._persistence_task: Optional[asyncio.Task] = None
        self._batch_persistence_queue: List[Dict[str, Any]] = []
        self._persistence_interval = 5.0  # Batch persistence every 5 seconds
        self._closed = False
        
        # Start async cleanup if enabled
        if auto_cleanup:
            self._start_async_cleanup()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the async signal manager."""
        if self._closed:
            return
        
        self._closed = True
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cancel persistence task
        if self._persistence_task and not self._persistence_task.done():
            self._persistence_task.cancel()
            try:
                await self._persistence_task
            except asyncio.CancelledError:
                pass
        
        # Final persistence
        await self.save_signals_async()
        
        logger.info("Async signal manager closed")
    
    async def create_signal_async(
        self,
        symbol: str,
        signal_type: SignalType,
        value: Union[bool, int, float],
        confidence: float = 0.5,
        strength: float = 0.0,
        strategy_name: str = "",
        source_indicator: str = "",
        conditions_met: List[str] = None,
        expires_in_minutes: Optional[int] = None,
        validation_rules: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> Signal:
        """Create signal asynchronously."""
        async with self._async_lock:
            signal = self.create_signal(
                symbol, signal_type, value, confidence, strength,
                strategy_name, source_indicator, conditions_met,
                expires_in_minutes, validation_rules, metadata
            )
            
            # Queue for batch persistence
            await self._queue_for_persistence({
                'action': 'create_signal',
                'signal': signal.to_dict(),
                'timestamp': datetime.now().isoformat()
            })
            
            return signal
    
    async def update_signal_async(
        self,
        symbol: str,
        signal_type: SignalType,
        value: Union[bool, int, float],
        confidence: float = None,
        strength: float = None,
        conditions_met: List[str] = None
    ) -> Optional[Signal]:
        """Update signal asynchronously."""
        async with self._async_lock:
            signal = self.update_signal(
                symbol, signal_type, value, confidence, strength, conditions_met
            )
            
            if signal:
                # Queue for batch persistence
                await self._queue_for_persistence({
                    'action': 'update_signal',
                    'signal': signal.to_dict(),
                    'timestamp': datetime.now().isoformat()
                })
            
            return signal
    
    async def get_active_signal_async(self, symbol: str, signal_type: SignalType) -> Optional[Signal]:
        """Get active signal asynchronously."""
        async with self._async_lock:
            return self.get_active_signal(symbol, signal_type)
    
    async def get_all_active_signals_async(self, symbol: str) -> Dict[SignalType, Signal]:
        """Get all active signals for a symbol asynchronously."""
        async with self._async_lock:
            return self.get_all_active_signals(symbol)
    
    async def confirm_signal_async(self, symbol: str, signal_type: SignalType, reason: str = "") -> bool:
        """Confirm signal asynchronously."""
        async with self._async_lock:
            result = self.confirm_signal(symbol, signal_type, reason)
            
            if result:
                # Queue for batch persistence
                await self._queue_for_persistence({
                    'action': 'confirm_signal',
                    'symbol': symbol,
                    'signal_type': signal_type.value,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
            
            return result
    
    async def cancel_signal_async(self, symbol: str, signal_type: SignalType, reason: str = "") -> bool:
        """Cancel signal asynchronously."""
        async with self._async_lock:
            result = self.cancel_signal(symbol, signal_type, reason)
            
            if result:
                # Queue for batch persistence
                await self._queue_for_persistence({
                    'action': 'cancel_signal',
                    'symbol': symbol,
                    'signal_type': signal_type.value,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
            
            return result
    
    async def validate_signal_combination_async(
        self,
        symbol: str,
        required_signals: List[SignalType]
    ) -> bool:
        """Validate signal combination asynchronously."""
        async with self._async_lock:
            return self.validate_signal_combination(symbol, required_signals)
    
    async def get_signal_statistics_async(
        self,
        symbol: str,
        signal_type: Optional[SignalType] = None
    ) -> Dict[str, Any]:
        """Get signal statistics asynchronously."""
        async with self._async_lock:
            return self.get_signal_statistics(symbol, signal_type)
    
    async def reset_symbol_signals_async(self, symbol: str):
        """Reset all signals for a symbol asynchronously."""
        async with self._async_lock:
            self.reset_symbol_signals(symbol)
            
            # Queue for batch persistence
            await self._queue_for_persistence({
                'action': 'reset_symbol_signals',
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            })
    
    async def cleanup_expired_signals_async(self):
        """Clean up expired signals asynchronously."""
        async with self._async_lock:
            # Get expired signals before cleanup
            expired_signals = []
            for symbol, signals in self._active_signals.items():
                for signal_type, signal in signals.items():
                    if not signal.is_valid():
                        expired_signals.append({
                            'symbol': symbol,
                            'signal_type': signal_type.value,
                            'signal_id': signal.signal_id
                        })
            
            # Perform cleanup
            self.cleanup_expired_signals()
            
            # Queue for batch persistence if any signals were expired
            if expired_signals:
                await self._queue_for_persistence({
                    'action': 'cleanup_expired_signals',
                    'expired_signals': expired_signals,
                    'timestamp': datetime.now().isoformat()
                })
    
    async def save_signals_async(self, file_path: Optional[str] = None) -> bool:
        """Save signals to file asynchronously."""
        save_path = file_path or self._persistence_file
        if not save_path:
            return False
        
        async with self._async_lock:
            try:
                data = {
                    "signal_histories": {
                        symbol: {
                            "symbol": history.symbol,
                            "signals": [signal.to_dict() for signal in history.signals],
                            "max_history_size": history.max_history_size
                        }
                        for symbol, history in self._signal_histories.items()
                    },
                    "active_signals": {
                        symbol: {
                            signal_type.value: signal.to_dict()
                            for signal_type, signal in signals.items()
                        }
                        for symbol, signals in self._active_signals.items()
                    },
                    "saved_at": datetime.now().isoformat()
                }
                
                # Write file asynchronously
                async with aiofiles.open(save_path, 'w') as f:
                    await f.write(json.dumps(data, indent=2))
                
                logger.debug(f"Signals saved to {save_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save signals: {e}")
                return False
    
    async def load_signals_async(self, file_path: Optional[str] = None) -> bool:
        """Load signals from file asynchronously."""
        load_path = file_path or self._persistence_file
        if not load_path or not Path(load_path).exists():
            return False
        
        async with self._async_lock:
            try:
                # Read file asynchronously
                async with aiofiles.open(load_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                
                # Load signal histories
                self._signal_histories = {}
                for symbol, history_data in data.get("signal_histories", {}).items():
                    history = SignalHistory(
                        symbol=history_data["symbol"],
                        max_history_size=history_data.get("max_history_size", 1000)
                    )
                    history.signals = [
                        Signal.from_dict(signal_data)
                        for signal_data in history_data["signals"]
                    ]
                    self._signal_histories[symbol] = history
                
                # Load active signals
                self._active_signals = {}
                for symbol, signals_data in data.get("active_signals", {}).items():
                    self._active_signals[symbol] = {}
                    for signal_type_str, signal_data in signals_data.items():
                        signal_type = SignalType(signal_type_str)
                        signal = Signal.from_dict(signal_data)
                        self._active_signals[symbol][signal_type] = signal
                
                logger.debug(f"Signals loaded from {load_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load signals: {e}")
                return False
    
    async def _queue_for_persistence(self, operation: Dict[str, Any]):
        """Queue operation for batch persistence."""
        self._batch_persistence_queue.append(operation)
        
        # Start persistence task if not running
        if self._persistence_task is None or self._persistence_task.done():
            self._persistence_task = asyncio.create_task(self._batch_persistence_worker())
    
    async def _batch_persistence_worker(self):
        """Worker for batch persistence operations."""
        while not self._closed and self._batch_persistence_queue:
            try:
                # Wait for batch interval or until queue has enough items
                await asyncio.sleep(self._persistence_interval)
                
                if self._batch_persistence_queue:
                    # Process batch
                    batch = self._batch_persistence_queue.copy()
                    self._batch_persistence_queue.clear()
                    
                    # Save current state
                    await self.save_signals_async()
                    
                    logger.debug(f"Processed batch persistence with {len(batch)} operations")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch persistence worker: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    def _start_async_cleanup(self):
        """Start async cleanup task."""
        async def cleanup_worker():
            while not self._closed:
                try:
                    await asyncio.sleep(300)  # Run every 5 minutes
                    await self.cleanup_expired_signals_async()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Async cleanup worker error: {e}")
        
        task_manager = get_task_manager()
        self._cleanup_task = task_manager.create_task(
            cleanup_worker(),
            name="signal_cleanup",
            group="signal_manager"
        )
    
    # Batch operations for multiple symbols
    
    async def process_multiple_signals_async(
        self,
        signal_operations: List[Dict[str, Any]]
    ) -> List[Optional[Signal]]:
        """Process multiple signal operations concurrently."""
        async def process_operation(operation):
            op_type = operation.get('type')
            symbol = operation.get('symbol')
            signal_type = operation.get('signal_type')
            
            if op_type == 'create':
                return await self.create_signal_async(
                    symbol=symbol,
                    signal_type=signal_type,
                    value=operation.get('value'),
                    confidence=operation.get('confidence', 0.5),
                    strength=operation.get('strength', 0.0),
                    strategy_name=operation.get('strategy_name', ''),
                    source_indicator=operation.get('source_indicator', ''),
                    conditions_met=operation.get('conditions_met'),
                    expires_in_minutes=operation.get('expires_in_minutes'),
                    validation_rules=operation.get('validation_rules'),
                    metadata=operation.get('metadata')
                )
            elif op_type == 'update':
                return await self.update_signal_async(
                    symbol=symbol,
                    signal_type=signal_type,
                    value=operation.get('value'),
                    confidence=operation.get('confidence'),
                    strength=operation.get('strength'),
                    conditions_met=operation.get('conditions_met')
                )
            elif op_type == 'confirm':
                await self.confirm_signal_async(
                    symbol=symbol,
                    signal_type=signal_type,
                    reason=operation.get('reason', '')
                )
                return None
            elif op_type == 'cancel':
                await self.cancel_signal_async(
                    symbol=symbol,
                    signal_type=signal_type,
                    reason=operation.get('reason', '')
                )
                return None
            else:
                logger.warning(f"Unknown operation type: {op_type}")
                return None
        
        # Process operations concurrently
        tasks = [process_operation(op) for op in signal_operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing signal operation {i}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_signals_for_multiple_symbols_async(
        self,
        symbols: List[str],
        signal_types: List[SignalType] = None
    ) -> Dict[str, Dict[SignalType, Signal]]:
        """Get signals for multiple symbols concurrently."""
        async def get_symbol_signals(symbol):
            if signal_types:
                signals = {}
                for signal_type in signal_types:
                    signal = await self.get_active_signal_async(symbol, signal_type)
                    if signal:
                        signals[signal_type] = signal
                return signals
            else:
                return await self.get_all_active_signals_async(symbol)
        
        # Process symbols concurrently
        tasks = [get_symbol_signals(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results
        symbol_signals = {}
        for i, symbol in enumerate(symbols):
            if isinstance(results[i], Exception):
                logger.error(f"Error getting signals for {symbol}: {results[i]}")
                symbol_signals[symbol] = {}
            else:
                symbol_signals[symbol] = results[i]
        
        return symbol_signals


# Global async signal manager instance
_async_signal_manager: Optional[AsyncSignalManager] = None


def get_async_signal_manager() -> AsyncSignalManager:
    """Get the global async signal manager instance."""
    global _async_signal_manager
    if _async_signal_manager is None:
        raise RuntimeError("Async signal manager not initialized. Call initialize_async_signal_manager() first.")
    return _async_signal_manager


def initialize_async_signal_manager(
    persistence_file: Optional[str] = None,
    auto_cleanup: bool = True
) -> AsyncSignalManager:
    """Initialize the global async signal manager."""
    global _async_signal_manager
    _async_signal_manager = AsyncSignalManager(
        persistence_file=persistence_file,
        auto_cleanup=auto_cleanup
    )
    return _async_signal_manager


async def cleanup_async_signal_manager():
    """Clean up the global async signal manager."""
    global _async_signal_manager
    if _async_signal_manager:
        await _async_signal_manager.close()
        _async_signal_manager = None


# Convenience async functions for backward compatibility
async def create_buy_signal_async(symbol: str, value: Union[bool, int], confidence: float = 0.5, **kwargs) -> Signal:
    """Create a buy signal asynchronously."""
    return await get_async_signal_manager().create_signal_async(symbol, SignalType.BUY, value, confidence, **kwargs)


async def create_sell_signal_async(symbol: str, value: Union[bool, int], confidence: float = 0.5, **kwargs) -> Signal:
    """Create a sell signal asynchronously."""
    return await get_async_signal_manager().create_signal_async(symbol, SignalType.SELL, value, confidence, **kwargs)


async def create_trend_signal_async(symbol: str, value: bool, confidence: float = 0.5, **kwargs) -> Signal:
    """Create a trend signal asynchronously."""
    return await get_async_signal_manager().create_signal_async(symbol, SignalType.TREND, value, confidence, **kwargs)


async def get_buy_signal_async(symbol: str, default_value: Union[bool, int] = False) -> Union[bool, int]:
    """Get buy signal value asynchronously."""
    signal = await get_async_signal_manager().get_active_signal_async(symbol, SignalType.BUY)
    return signal.value if signal else default_value


async def get_sell_signal_async(symbol: str, default_value: Union[bool, int] = False) -> Union[bool, int]:
    """Get sell signal value asynchronously."""
    signal = await get_async_signal_manager().get_active_signal_async(symbol, SignalType.SELL)
    return signal.value if signal else default_value


async def get_trend_signal_async(symbol: str, default_value: bool = False) -> bool:
    """Get trend signal value asynchronously."""
    signal = await get_async_signal_manager().get_active_signal_async(symbol, SignalType.TREND)
    return signal.value if signal else default_value 