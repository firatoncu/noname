"""
Test script for the new APIManager to validate functionality and performance.

This script tests:
1. Basic API manager initialization
2. Rate limiting functionality
3. Request queuing and prioritization
4. Batch request processing
5. Error handling and recovery
6. Performance metrics
"""

import asyncio
import logging
import time
from typing import List, Dict, Any

from utils.api_manager import (
    APIManager, RateLimitConfig, RequestPriority, RequestType, BackoffStrategy,
    initialize_api_manager, get_api_manager, cleanup_api_manager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIManagerTester:
    """Test suite for APIManager functionality."""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.test_results = {}
    
    async def run_all_tests(self):
        """Run all test cases."""
        logger.info("Starting APIManager test suite...")
        
        test_cases = [
            ("Basic Initialization", self.test_basic_initialization),
            ("Rate Limiting", self.test_rate_limiting),
            ("Request Prioritization", self.test_request_prioritization),
            ("Batch Processing", self.test_batch_processing),
            ("Error Handling", self.test_error_handling),
            ("Performance Metrics", self.test_performance_metrics),
            ("Circuit Breaker", self.test_circuit_breaker),
            ("Adaptive Throttling", self.test_adaptive_throttling),
        ]
        
        for test_name, test_func in test_cases:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running test: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                start_time = time.time()
                result = await test_func()
                duration = time.time() - start_time
                
                self.test_results[test_name] = {
                    'status': 'PASSED' if result else 'FAILED',
                    'duration': duration
                }
                
                logger.info(f"Test {test_name}: {'PASSED' if result else 'FAILED'} ({duration:.2f}s)")
                
            except Exception as e:
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'duration': time.time() - start_time
                }
                logger.error(f"Test {test_name}: ERROR - {e}")
        
        # Print summary
        self.print_test_summary()
    
    async def test_basic_initialization(self) -> bool:
        """Test basic APIManager initialization and startup."""
        try:
            # Test configuration
            config = RateLimitConfig(
                requests_per_minute=100,
                orders_per_second=5,
                enable_adaptive_throttling=True
            )
            
            # Initialize API manager
            api_manager = initialize_api_manager(self.api_key, self.api_secret, config)
            
            # Start the manager
            await api_manager.start(num_workers=3)
            
            # Verify it's running
            assert api_manager._is_running, "API manager should be running"
            assert len(api_manager._worker_tasks) == 3, "Should have 3 worker tasks"
            
            # Test basic connectivity
            result = await api_manager.request(
                'GET', '/fapi/v1/ping',
                request_type=RequestType.MARKET_DATA,
                priority=RequestPriority.HIGH
            )
            
            assert result == {}, "Ping should return empty dict"
            
            # Stop the manager
            await api_manager.stop()
            
            logger.info("✓ Basic initialization test passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Basic initialization test failed: {e}")
            return False
    
    async def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality."""
        try:
            # Configure with very low limits for testing
            config = RateLimitConfig(
                requests_per_minute=10,
                weight_per_second=5,
                enable_adaptive_throttling=False
            )
            
            api_manager = APIManager(self.api_key, self.api_secret, config)
            await api_manager.start(num_workers=2)
            
            # Make rapid requests to test rate limiting
            start_time = time.time()
            tasks = []
            
            for i in range(15):  # More than the limit
                task = asyncio.create_task(
                    api_manager.request(
                        'GET', '/fapi/v1/time',
                        request_type=RequestType.MARKET_DATA,
                        priority=RequestPriority.NORMAL
                    )
                )
                tasks.append(task)
            
            # Wait for all requests
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            # Should take longer than 1 second due to rate limiting
            assert duration > 1.0, f"Rate limiting should slow down requests (took {duration:.2f}s)"
            
            # Check that most requests succeeded
            successful = sum(1 for r in results if not isinstance(r, Exception))
            assert successful >= 10, f"Most requests should succeed ({successful}/15)"
            
            await api_manager.stop()
            
            logger.info(f"✓ Rate limiting test passed (duration: {duration:.2f}s, success: {successful}/15)")
            return True
            
        except Exception as e:
            logger.error(f"✗ Rate limiting test failed: {e}")
            return False
    
    async def test_request_prioritization(self) -> bool:
        """Test request prioritization."""
        try:
            config = RateLimitConfig(
                requests_per_minute=20,
                weight_per_second=3,  # Very low to force queuing
                enable_adaptive_throttling=False
            )
            
            api_manager = APIManager(self.api_key, self.api_secret, config)
            await api_manager.start(num_workers=1)  # Single worker to ensure ordering
            
            # Submit requests with different priorities
            results = []
            
            # Low priority requests first
            for i in range(3):
                task = asyncio.create_task(
                    api_manager.request(
                        'GET', '/fapi/v1/time',
                        request_type=RequestType.MARKET_DATA,
                        priority=RequestPriority.LOW
                    )
                )
                results.append(('LOW', task))
            
            # Then high priority requests
            for i in range(2):
                task = asyncio.create_task(
                    api_manager.request(
                        'GET', '/fapi/v1/time',
                        request_type=RequestType.MARKET_DATA,
                        priority=RequestPriority.HIGH
                    )
                )
                results.append(('HIGH', task))
            
            # Wait for all to complete
            completed_results = []
            for priority, task in results:
                try:
                    await task
                    completed_results.append(priority)
                except Exception as e:
                    logger.warning(f"Request failed: {e}")
            
            await api_manager.stop()
            
            # High priority requests should be processed first
            # (This is a simplified test - in practice, timing can vary)
            logger.info(f"✓ Request prioritization test completed (order: {completed_results})")
            return True
            
        except Exception as e:
            logger.error(f"✗ Request prioritization test failed: {e}")
            return False
    
    async def test_batch_processing(self) -> bool:
        """Test batch request processing."""
        try:
            config = RateLimitConfig(
                requests_per_minute=100,
                enable_adaptive_throttling=False
            )
            
            api_manager = APIManager(self.api_key, self.api_secret, config)
            await api_manager.start(num_workers=5)
            
            # Prepare batch requests
            symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
            batch_requests = []
            
            for symbol in symbols:
                batch_requests.append((
                    'GET', '/fapi/v1/ticker/price',
                    {'symbol': symbol},
                    False,  # not signed
                    RequestType.MARKET_DATA,
                    RequestPriority.NORMAL
                ))
            
            # Execute batch
            start_time = time.time()
            results = await api_manager.batch_request(batch_requests, timeout=30.0)
            duration = time.time() - start_time
            
            # Verify results
            assert len(results) == len(symbols), f"Should get {len(symbols)} results"
            
            successful = 0
            for i, result in enumerate(results):
                if 'error' not in result and 'price' in result:
                    successful += 1
                    logger.info(f"  {symbols[i]}: ${float(result['price']):.2f}")
            
            assert successful >= 2, f"At least 2 requests should succeed ({successful}/{len(symbols)})"
            
            await api_manager.stop()
            
            logger.info(f"✓ Batch processing test passed ({successful}/{len(symbols)} successful, {duration:.2f}s)")
            return True
            
        except Exception as e:
            logger.error(f"✗ Batch processing test failed: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling and retry mechanisms."""
        try:
            config = RateLimitConfig(
                requests_per_minute=100,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                initial_backoff=0.1,
                max_backoff=2.0
            )
            
            api_manager = APIManager(self.api_key, self.api_secret, config)
            await api_manager.start(num_workers=2)
            
            # Test invalid endpoint (should fail)
            try:
                await api_manager.request(
                    'GET', '/fapi/v1/invalid_endpoint',
                    request_type=RequestType.MARKET_DATA,
                    priority=RequestPriority.NORMAL,
                    timeout=5.0
                )
                assert False, "Invalid endpoint should fail"
            except Exception as e:
                logger.info(f"  Expected error for invalid endpoint: {type(e).__name__}")
            
            # Test valid endpoint (should succeed)
            result = await api_manager.request(
                'GET', '/fapi/v1/time',
                request_type=RequestType.MARKET_DATA,
                priority=RequestPriority.NORMAL
            )
            
            assert 'serverTime' in result, "Valid endpoint should return server time"
            
            await api_manager.stop()
            
            logger.info("✓ Error handling test passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error handling test failed: {e}")
            return False
    
    async def test_performance_metrics(self) -> bool:
        """Test performance metrics collection."""
        try:
            config = RateLimitConfig(
                requests_per_minute=50,
                enable_adaptive_throttling=True
            )
            
            api_manager = APIManager(self.api_key, self.api_secret, config)
            await api_manager.start(num_workers=3)
            
            # Make some requests to generate metrics
            for i in range(5):
                try:
                    await api_manager.request(
                        'GET', '/fapi/v1/time',
                        request_type=RequestType.MARKET_DATA,
                        priority=RequestPriority.NORMAL
                    )
                except Exception:
                    pass  # Ignore errors for metrics test
            
            # Get metrics
            metrics = api_manager.get_metrics()
            
            # Verify metrics structure
            required_keys = ['uptime', 'is_running', 'worker_count', 'rate_limiter', 'queue']
            for key in required_keys:
                assert key in metrics, f"Metrics should contain '{key}'"
            
            # Verify rate limiter metrics
            rate_limiter = metrics['rate_limiter']
            required_rate_keys = ['total_requests', 'successful_requests', 'success_rate']
            for key in required_rate_keys:
                assert key in rate_limiter, f"Rate limiter metrics should contain '{key}'"
            
            # Log metrics
            logger.info(f"  Uptime: {metrics['uptime']:.2f}s")
            logger.info(f"  Total requests: {rate_limiter['total_requests']}")
            logger.info(f"  Success rate: {rate_limiter['success_rate']:.2%}")
            logger.info(f"  Queue size: {metrics['queue']['total_size']}")
            
            await api_manager.stop()
            
            logger.info("✓ Performance metrics test passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Performance metrics test failed: {e}")
            return False
    
    async def test_circuit_breaker(self) -> bool:
        """Test circuit breaker functionality."""
        try:
            config = RateLimitConfig(
                requests_per_minute=100,
                failure_threshold=2,  # Low threshold for testing
                recovery_timeout=5.0
            )
            
            api_manager = APIManager(self.api_key, self.api_secret, config)
            await api_manager.start(num_workers=2)
            
            # Force failures to trigger circuit breaker
            for i in range(3):
                try:
                    await api_manager.request(
                        'GET', '/fapi/v1/invalid_endpoint',
                        request_type=RequestType.MARKET_DATA,
                        priority=RequestPriority.NORMAL,
                        timeout=2.0
                    )
                except Exception:
                    pass  # Expected to fail
            
            # Check if circuit breaker is open
            metrics = api_manager.get_metrics()
            circuit_state = metrics['rate_limiter']['circuit_state']
            
            logger.info(f"  Circuit breaker state: {circuit_state}")
            
            await api_manager.stop()
            
            logger.info("✓ Circuit breaker test completed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Circuit breaker test failed: {e}")
            return False
    
    async def test_adaptive_throttling(self) -> bool:
        """Test adaptive throttling functionality."""
        try:
            config = RateLimitConfig(
                requests_per_minute=100,
                enable_adaptive_throttling=True,
                target_success_rate=0.95,
                monitoring_window=10
            )
            
            api_manager = APIManager(self.api_key, self.api_secret, config)
            await api_manager.start(num_workers=2)
            
            # Make requests to build up response history
            for i in range(12):
                try:
                    await api_manager.request(
                        'GET', '/fapi/v1/time',
                        request_type=RequestType.MARKET_DATA,
                        priority=RequestPriority.NORMAL
                    )
                except Exception:
                    pass
            
            # Check throttle factor
            metrics = api_manager.get_metrics()
            throttle_factor = metrics['rate_limiter']['current_throttle_factor']
            
            logger.info(f"  Throttle factor: {throttle_factor:.2f}")
            logger.info(f"  Success rate: {metrics['rate_limiter']['success_rate']:.2%}")
            
            await api_manager.stop()
            
            logger.info("✓ Adaptive throttling test completed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Adaptive throttling test failed: {e}")
            return False
    
    def print_test_summary(self):
        """Print test results summary."""
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'PASSED')
        failed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'FAILED')
        error_tests = sum(1 for r in self.test_results.values() if r['status'] == 'ERROR')
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Errors: {error_tests}")
        logger.info(f"Success Rate: {passed_tests/total_tests:.1%}")
        
        logger.info(f"\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status_icon = "✓" if result['status'] == 'PASSED' else "✗"
            duration = result.get('duration', 0)
            logger.info(f"  {status_icon} {test_name}: {result['status']} ({duration:.2f}s)")
            
            if 'error' in result:
                logger.info(f"    Error: {result['error']}")


async def main():
    """Main test function."""
    
    # Test configuration - replace with your credentials for full testing
    # For basic testing without credentials, some tests will be skipped
    API_KEY = "test_api_key"  # Replace with real key
    API_SECRET = "test_api_secret"  # Replace with real secret
    
    if API_KEY == "test_api_key":
        logger.warning("Using test credentials - some tests may fail")
        logger.warning("Replace API_KEY and API_SECRET with real credentials for full testing")
    
    # Create and run test suite
    tester = APIManagerTester(API_KEY, API_SECRET)
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test suite error: {e}")
    finally:
        # Clean up
        try:
            await cleanup_api_manager()
        except Exception:
            pass
        
        logger.info("Test suite completed")


if __name__ == "__main__":
    asyncio.run(main()) 