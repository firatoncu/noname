"""
Performance Testing Script for Trading Bot Optimizations

This script tests and benchmarks the performance improvements
implemented in the trading bot application.
"""

import asyncio
import time
import logging
import sys
from typing import List, Dict, Any
import pandas as pd
import numpy as np

# Import optimization modules with error handling
try:
    from utils.performance_optimizer import (
        get_cache_system, get_memory_optimizer, get_profiler, get_cpu_optimizer,
        cleanup_performance_optimizers
    )
    from utils.optimized_fetch_data import (
        get_data_fetcher, cleanup_data_fetcher
    )
    from utils.optimized_indicators import get_indicators
    from utils.optimized_database import (
        get_optimized_database, cleanup_database_optimizers
    )
    OPTIMIZATIONS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some optimization modules not available: {e}")
    OPTIMIZATIONS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceTester:
    """Performance testing and benchmarking class."""
    
    def __init__(self):
        if not OPTIMIZATIONS_AVAILABLE:
            logger.warning("Performance optimizations not available, running basic tests only")
            self.cache_system = None
            self.memory_optimizer = None
            self.profiler = None
            self.cpu_optimizer = None
            self.data_fetcher = None
            self.indicators = None
        else:
            self.cache_system = get_cache_system()
            self.memory_optimizer = get_memory_optimizer()
            self.profiler = get_profiler()
            self.cpu_optimizer = get_cpu_optimizer()
            self.data_fetcher = get_data_fetcher()
            self.indicators = get_indicators()
        self.results = {}
    
    async def test_cache_performance(self, iterations: int = 1000):
        """Test cache performance with various operations."""
        if not self.cache_system:
            logger.warning("Cache system not available, skipping cache test")
            return
            
        logger.info(f"Testing cache performance with {iterations} iterations")
        
        # Test cache set operations
        start_time = time.time()
        for i in range(iterations):
            await self.cache_system.set(f"key_{i}", f"value_{i}")
        set_time = time.time() - start_time
        
        # Test cache get operations
        start_time = time.time()
        hits = 0
        for i in range(iterations):
            result = await self.cache_system.get(f"key_{i}")
            if result is not None:
                hits += 1
        get_time = time.time() - start_time
        
        hit_rate = hits / iterations
        
        self.results['cache'] = {
            'set_time': set_time,
            'get_time': get_time,
            'hit_rate': hit_rate,
            'ops_per_second_set': iterations / set_time,
            'ops_per_second_get': iterations / get_time
        }
        
        logger.info(f"Cache test completed - Hit rate: {hit_rate:.2%}, "
                   f"Set: {iterations/set_time:.0f} ops/s, Get: {iterations/get_time:.0f} ops/s")
    
    def test_memory_optimization(self):
        """Test memory optimization features."""
        if not self.memory_optimizer:
            logger.warning("Memory optimizer not available, skipping memory test")
            return
            
        logger.info("Testing memory optimization")
        
        # Get initial memory stats
        initial_stats = self.memory_optimizer.get_memory_usage()
        
        # Create large DataFrames to test memory optimization
        large_dfs = []
        for i in range(10):
            df = pd.DataFrame({
                'timestamp': pd.date_range('2023-01-01', periods=10000, freq='1min'),
                'open': np.random.random(10000) * 100,
                'high': np.random.random(10000) * 100,
                'low': np.random.random(10000) * 100,
                'close': np.random.random(10000) * 100,
                'volume': np.random.random(10000) * 1000000
            })
            large_dfs.append(df)
        
        # Memory stats after creating DataFrames
        after_creation_stats = self.memory_optimizer.get_memory_usage()
        
        # Optimize DataFrames
        start_time = time.time()
        optimized_dfs = []
        for df in large_dfs:
            optimized_df = self.memory_optimizer.optimize_dataframe(df)
            optimized_dfs.append(optimized_df)
        optimization_time = time.time() - start_time
        
        # Force garbage collection
        collected = self.memory_optimizer.force_garbage_collection()
        
        # Final memory stats
        final_stats = self.memory_optimizer.get_memory_usage()
        
        memory_saved = after_creation_stats['rss_mb'] - final_stats['rss_mb']
        
        self.results['memory'] = {
            'initial_memory_mb': initial_stats['rss_mb'],
            'peak_memory_mb': after_creation_stats['rss_mb'],
            'final_memory_mb': final_stats['rss_mb'],
            'memory_saved_mb': memory_saved,
            'optimization_time': optimization_time,
            'objects_collected': collected
        }
        
        logger.info(f"Memory test completed - Saved: {memory_saved:.1f}MB, "
                   f"Collected: {collected} objects")
    
    async def test_cpu_optimization(self, iterations: int = 100):
        """Test CPU optimization with thread and process pools."""
        logger.info(f"Testing CPU optimization with {iterations} iterations")
        
        def cpu_intensive_task(n: int) -> int:
            """CPU-intensive task for testing."""
            result = 0
            for i in range(n * 1000):
                result += i ** 2
            return result
        
        # Test without optimization (sequential)
        start_time = time.time()
        sequential_results = []
        for i in range(iterations):
            result = cpu_intensive_task(100)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        # Test with thread pool
        start_time = time.time()
        thread_tasks = []
        for i in range(iterations):
            task = self.cpu_optimizer.run_in_thread(cpu_intensive_task, 100)
            thread_tasks.append(task)
        thread_results = await asyncio.gather(*thread_tasks)
        thread_time = time.time() - start_time
        
        # Test with process pool (smaller batch due to overhead)
        small_iterations = min(iterations // 4, 25)
        start_time = time.time()
        process_tasks = []
        for i in range(small_iterations):
            task = self.cpu_optimizer.run_in_process(cpu_intensive_task, 100)
            process_tasks.append(task)
        process_results = await asyncio.gather(*process_tasks)
        process_time = time.time() - start_time
        
        self.results['cpu'] = {
            'sequential_time': sequential_time,
            'thread_time': thread_time,
            'process_time': process_time,
            'thread_speedup': sequential_time / thread_time,
            'process_speedup': (sequential_time / iterations * small_iterations) / process_time,
            'iterations': iterations,
            'small_iterations': small_iterations
        }
        
        logger.info(f"CPU test completed - Thread speedup: {sequential_time/thread_time:.2f}x, "
                   f"Process speedup: {(sequential_time/iterations*small_iterations)/process_time:.2f}x")
    
    def test_indicator_optimization(self, data_size: int = 1000):
        """Test technical indicator optimization."""
        logger.info(f"Testing indicator optimization with {data_size} data points")
        
        # Generate test data
        close_prices = pd.Series(np.random.random(data_size) * 100 + 50)
        high_prices = close_prices + np.random.random(data_size) * 5
        low_prices = close_prices - np.random.random(data_size) * 5
        
        # Test MACD calculation
        start_time = time.time()
        macd_data = self.indicators.calculate_macd(close_prices, symbol="TEST")
        macd_time = time.time() - start_time
        
        # Test RSI calculation
        start_time = time.time()
        rsi_data = self.indicators.calculate_rsi(close_prices, symbol="TEST")
        rsi_time = time.time() - start_time
        
        # Test Bollinger Bands calculation
        start_time = time.time()
        bb_data = self.indicators.calculate_bollinger_bands(close_prices, symbol="TEST")
        bb_time = time.time() - start_time
        
        # Test Fibonacci levels calculation
        start_time = time.time()
        fib_data = self.indicators.calculate_fibonacci_levels(high_prices, low_prices, symbol="TEST")
        fib_time = time.time() - start_time
        
        # Test cached calculations (should be faster)
        start_time = time.time()
        cached_macd = self.indicators.calculate_macd(close_prices, symbol="TEST")
        cached_macd_time = time.time() - start_time
        
        self.results['indicators'] = {
            'data_size': data_size,
            'macd_time': macd_time,
            'rsi_time': rsi_time,
            'bollinger_time': bb_time,
            'fibonacci_time': fib_time,
            'cached_macd_time': cached_macd_time,
            'cache_speedup': macd_time / cached_macd_time if cached_macd_time > 0 else float('inf')
        }
        
        logger.info(f"Indicator test completed - MACD: {macd_time:.3f}s, "
                   f"Cache speedup: {macd_time/cached_macd_time:.1f}x")
    
    async def test_database_optimization(self):
        """Test database optimization features."""
        logger.info("Testing database optimization")
        
        db = get_optimized_database()
        
        # Test query caching (simulated)
        test_queries = [
            "SELECT * FROM test_table WHERE id = 1",
            "SELECT * FROM test_table WHERE id = 2",
            "SELECT * FROM test_table WHERE id = 1",  # Should hit cache
        ]
        
        query_times = []
        for query in test_queries:
            start_time = time.time()
            # Simulate query execution
            await asyncio.sleep(0.01)  # Simulate database latency
            query_time = time.time() - start_time
            query_times.append(query_time)
        
        # Test batch operations (simulated)
        batch_data = [{"id": i, "value": f"test_{i}"} for i in range(1000)]
        
        start_time = time.time()
        await db.batch_insert("test_table", batch_data)
        batch_time = time.time() - start_time
        
        self.results['database'] = {
            'query_times': query_times,
            'avg_query_time': np.mean(query_times),
            'batch_insert_time': batch_time,
            'batch_size': len(batch_data)
        }
        
        logger.info(f"Database test completed - Avg query: {np.mean(query_times):.3f}s, "
                   f"Batch insert: {batch_time:.3f}s")
    
    async def run_comprehensive_test(self):
        """Run comprehensive performance test suite."""
        logger.info("Starting comprehensive performance test suite")
        
        start_time = time.time()
        
        # Initialize memory monitoring
        await self.memory_optimizer.start_monitoring()
        
        # Run all tests
        await self.test_cache_performance(1000)
        self.test_memory_optimization()
        await self.test_cpu_optimization(50)
        self.test_indicator_optimization(1000)
        await self.test_database_optimization()
        
        total_time = time.time() - start_time
        
        # Generate performance report
        self.generate_performance_report(total_time)
        
        return self.results
    
    def generate_performance_report(self, total_time: float):
        """Generate comprehensive performance report."""
        logger.info("=" * 60)
        logger.info("PERFORMANCE TEST RESULTS")
        logger.info("=" * 60)
        
        # Cache performance
        if 'cache' in self.results:
            cache = self.results['cache']
            logger.info(f"Cache Performance:")
            logger.info(f"  Hit Rate: {cache['hit_rate']:.2%}")
            logger.info(f"  Set Operations: {cache['ops_per_second_set']:.0f} ops/sec")
            logger.info(f"  Get Operations: {cache['ops_per_second_get']:.0f} ops/sec")
        
        # Memory optimization
        if 'memory' in self.results:
            memory = self.results['memory']
            logger.info(f"Memory Optimization:")
            logger.info(f"  Memory Saved: {memory['memory_saved_mb']:.1f} MB")
            logger.info(f"  Objects Collected: {memory['objects_collected']}")
            logger.info(f"  Optimization Time: {memory['optimization_time']:.3f}s")
        
        # CPU optimization
        if 'cpu' in self.results:
            cpu = self.results['cpu']
            logger.info(f"CPU Optimization:")
            logger.info(f"  Thread Pool Speedup: {cpu['thread_speedup']:.2f}x")
            logger.info(f"  Process Pool Speedup: {cpu['process_speedup']:.2f}x")
        
        # Indicator optimization
        if 'indicators' in self.results:
            indicators = self.results['indicators']
            logger.info(f"Indicator Optimization:")
            logger.info(f"  MACD Calculation: {indicators['macd_time']:.3f}s")
            logger.info(f"  Cache Speedup: {indicators['cache_speedup']:.1f}x")
        
        # Database optimization
        if 'database' in self.results:
            database = self.results['database']
            logger.info(f"Database Optimization:")
            logger.info(f"  Average Query Time: {database['avg_query_time']:.3f}s")
            logger.info(f"  Batch Insert Time: {database['batch_insert_time']:.3f}s")
        
        logger.info(f"Total Test Time: {total_time:.2f}s")
        logger.info("=" * 60)
    
    async def cleanup(self):
        """Clean up test resources."""
        await cleanup_performance_optimizers()
        await cleanup_data_fetcher()
        await cleanup_database_optimizers()


async def simple_performance_test():
    """Simple performance test that doesn't require all dependencies."""
    logger.info("Running simple performance test")
    
    # Test basic Python performance optimizations
    logger.info("Testing basic list operations...")
    
    # Test list comprehension vs loop
    start_time = time.time()
    result1 = []
    for i in range(100000):
        result1.append(i * 2)
    loop_time = time.time() - start_time
    
    start_time = time.time()
    result2 = [i * 2 for i in range(100000)]
    comprehension_time = time.time() - start_time
    
    logger.info(f"Loop time: {loop_time:.3f}s, Comprehension time: {comprehension_time:.3f}s")
    logger.info(f"Comprehension speedup: {loop_time/comprehension_time:.2f}x")
    
    # Test NumPy vs pure Python
    logger.info("Testing NumPy vs pure Python...")
    
    data = list(range(100000))
    
    start_time = time.time()
    python_sum = sum(x * x for x in data)
    python_time = time.time() - start_time
    
    np_data = np.array(data)
    start_time = time.time()
    numpy_sum = np.sum(np_data * np_data)
    numpy_time = time.time() - start_time
    
    logger.info(f"Python time: {python_time:.3f}s, NumPy time: {numpy_time:.3f}s")
    logger.info(f"NumPy speedup: {python_time/numpy_time:.2f}x")
    
    # Test pandas DataFrame operations
    logger.info("Testing pandas DataFrame operations...")
    
    df = pd.DataFrame({
        'a': np.random.random(50000),
        'b': np.random.random(50000),
        'c': np.random.random(50000)
    })
    
    start_time = time.time()
    result = df['a'] * df['b'] + df['c']
    pandas_time = time.time() - start_time
    
    start_time = time.time()
    manual_result = []
    for i in range(len(df)):
        manual_result.append(df.iloc[i]['a'] * df.iloc[i]['b'] + df.iloc[i]['c'])
    manual_time = time.time() - start_time
    
    logger.info(f"Pandas time: {pandas_time:.3f}s, Manual time: {manual_time:.3f}s")
    if pandas_time > 0:
        logger.info(f"Pandas speedup: {manual_time/pandas_time:.2f}x")
    else:
        logger.info("Pandas speedup: >1000x (pandas operation was too fast to measure)")
    
    logger.info("Simple performance test completed!")


async def main():
    """Main function to run performance tests."""
    logger.info("Starting Performance Testing Suite")
    
    if not OPTIMIZATIONS_AVAILABLE:
        logger.info("Running simple performance test without optimizations")
        await simple_performance_test()
        return
    
    tester = PerformanceTester()
    
    try:
        await tester.run_comprehensive_test()
        
        # Generate and display report
        total_time = sum(
            result.get('total_time', 0) if isinstance(result, dict) else 0
            for result in tester.results.values()
        )
        
        tester.generate_performance_report(total_time)
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        logger.info("Falling back to simple performance test")
        await simple_performance_test()
    
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 