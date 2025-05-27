#!/usr/bin/env python3
"""
Comprehensive test runner for the n0name trading bot.

This script provides various test execution modes:
- Unit tests only
- Integration tests only
- All tests
- Performance tests
- Coverage reporting
- Parallel execution
- Custom test selection

Usage:
    python tests/run_tests.py --help
    python tests/run_tests.py --unit
    python tests/run_tests.py --integration
    python tests/run_tests.py --all
    python tests/run_tests.py --coverage
    python tests/run_tests.py --performance
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path
from typing import List, Optional
import time
from datetime import datetime


class TestRunner:
    """Comprehensive test runner with multiple execution modes."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.src_dir = self.project_root / "src"
        
    def run_command(self, cmd: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        print(f"Running: {' '.join(cmd)}")
        
        if capture_output:
            return subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        else:
            return subprocess.run(cmd, cwd=self.project_root)
    
    def run_unit_tests(self, verbose: bool = False, parallel: bool = False) -> int:
        """Run unit tests only."""
        print("🧪 Running Unit Tests...")
        
        cmd = ["python", "-m", "pytest", "-m", "unit"]
        
        if verbose:
            cmd.append("-v")
        
        if parallel:
            cmd.extend(["-n", "auto"])
        
        cmd.extend([
            "--tb=short",
            "--durations=10",
            "tests/unit/"
        ])
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_integration_tests(self, verbose: bool = False, parallel: bool = False) -> int:
        """Run integration tests only."""
        print("🔗 Running Integration Tests...")
        
        cmd = ["python", "-m", "pytest", "-m", "integration"]
        
        if verbose:
            cmd.append("-v")
        
        if parallel:
            cmd.extend(["-n", "auto"])
        
        cmd.extend([
            "--tb=short",
            "--durations=10",
            "tests/integration/"
        ])
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_performance_tests(self, verbose: bool = False) -> int:
        """Run performance tests."""
        print("⚡ Running Performance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "-m", "performance or slow",
            "--benchmark-only",
            "--benchmark-sort=mean",
            "--benchmark-columns=min,max,mean,stddev,rounds,iterations"
        ]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend([
            "--tb=short",
            "tests/"
        ])
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_all_tests(self, verbose: bool = False, parallel: bool = False) -> int:
        """Run all tests."""
        print("🚀 Running All Tests...")
        
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        if parallel:
            cmd.extend(["-n", "auto"])
        
        cmd.extend([
            "--tb=short",
            "--durations=10",
            "tests/"
        ])
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_with_coverage(self, test_type: str = "all", verbose: bool = False) -> int:
        """Run tests with coverage reporting."""
        print("📊 Running Tests with Coverage...")
        
        cmd = ["python", "-m", "pytest"]
        
        # Add test type marker
        if test_type == "unit":
            cmd.extend(["-m", "unit", "tests/unit/"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration", "tests/integration/"])
        else:
            cmd.append("tests/")
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-fail-under=80",
            "--tb=short"
        ])
        
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            print("\n✅ Coverage report generated:")
            print(f"  - HTML: {self.project_root}/htmlcov/index.html")
            print(f"  - XML: {self.project_root}/coverage.xml")
        
        return result.returncode
    
    def run_smoke_tests(self, verbose: bool = False) -> int:
        """Run smoke tests for quick validation."""
        print("💨 Running Smoke Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "-m", "smoke",
            "--tb=short",
            "--maxfail=5"
        ]
        
        if verbose:
            cmd.append("-v")
        
        cmd.append("tests/")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_security_tests(self, verbose: bool = False) -> int:
        """Run security-focused tests."""
        print("🔒 Running Security Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "-m", "security",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        cmd.append("tests/")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_custom_tests(self, pattern: str, verbose: bool = False) -> int:
        """Run tests matching a custom pattern."""
        print(f"🎯 Running Custom Tests: {pattern}")
        
        cmd = [
            "python", "-m", "pytest",
            "-k", pattern,
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        cmd.append("tests/")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def lint_code(self) -> int:
        """Run code linting."""
        print("🔍 Running Code Linting...")
        
        # Run ruff
        print("Running ruff...")
        ruff_result = self.run_command(["python", "-m", "ruff", "check", "src/", "tests/"])
        
        # Run mypy
        print("Running mypy...")
        mypy_result = self.run_command(["python", "-m", "mypy", "src/"])
        
        # Run black check
        print("Running black check...")
        black_result = self.run_command(["python", "-m", "black", "--check", "src/", "tests/"])
        
        # Return non-zero if any linter failed
        return max(ruff_result.returncode, mypy_result.returncode, black_result.returncode)
    
    def format_code(self) -> int:
        """Format code using black and isort."""
        print("🎨 Formatting Code...")
        
        # Run black
        print("Running black...")
        black_result = self.run_command(["python", "-m", "black", "src/", "tests/"])
        
        # Run isort
        print("Running isort...")
        isort_result = self.run_command(["python", "-m", "isort", "src/", "tests/"])
        
        return max(black_result.returncode, isort_result.returncode)
    
    def generate_test_report(self) -> int:
        """Generate comprehensive test report."""
        print("📋 Generating Test Report...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.project_root / f"test_reports_{timestamp}"
        report_dir.mkdir(exist_ok=True)
        
        cmd = [
            "python", "-m", "pytest",
            "--html", str(report_dir / "report.html"),
            "--self-contained-html",
            "--cov=src",
            "--cov-report=html:" + str(report_dir / "coverage"),
            "--cov-report=xml:" + str(report_dir / "coverage.xml"),
            "--junit-xml=" + str(report_dir / "junit.xml"),
            "--tb=short",
            "tests/"
        ]
        
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            print(f"\n✅ Test report generated in: {report_dir}")
            print(f"  - HTML Report: {report_dir}/report.html")
            print(f"  - Coverage: {report_dir}/coverage/index.html")
            print(f"  - JUnit XML: {report_dir}/junit.xml")
        
        return result.returncode
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        print("🔧 Checking Dependencies...")
        
        required_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-mock",
            "pytest-xdist",
            "pytest-html",
            "pytest-benchmark",
            "ruff",
            "mypy",
            "black",
            "isort"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            print("Install them with: pip install -e .[dev]")
            return False
        
        print("✅ All dependencies are installed")
        return True


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for n0name trading bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py --unit                    # Run unit tests only
  python tests/run_tests.py --integration             # Run integration tests only
  python tests/run_tests.py --all                     # Run all tests
  python tests/run_tests.py --coverage                # Run with coverage
  python tests/run_tests.py --performance             # Run performance tests
  python tests/run_tests.py --smoke                   # Run smoke tests
  python tests/run_tests.py --security                # Run security tests
  python tests/run_tests.py --custom "test_trading"   # Run custom pattern
  python tests/run_tests.py --lint                    # Run linting
  python tests/run_tests.py --format                  # Format code
  python tests/run_tests.py --report                  # Generate full report
        """
    )
    
    # Test execution modes
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--unit", action="store_true", help="Run unit tests only")
    test_group.add_argument("--integration", action="store_true", help="Run integration tests only")
    test_group.add_argument("--all", action="store_true", help="Run all tests")
    test_group.add_argument("--performance", action="store_true", help="Run performance tests")
    test_group.add_argument("--smoke", action="store_true", help="Run smoke tests")
    test_group.add_argument("--security", action="store_true", help="Run security tests")
    test_group.add_argument("--custom", metavar="PATTERN", help="Run tests matching pattern")
    
    # Coverage and reporting
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    
    # Code quality
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--format", action="store_true", help="Format code")
    
    # Options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-p", "--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies only")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Check dependencies first
    if not runner.check_dependencies():
        return 1
    
    if args.check_deps:
        return 0
    
    start_time = time.time()
    exit_code = 0
    
    try:
        if args.lint:
            exit_code = runner.lint_code()
        elif args.format:
            exit_code = runner.format_code()
        elif args.report:
            exit_code = runner.generate_test_report()
        elif args.unit:
            if args.coverage:
                exit_code = runner.run_with_coverage("unit", args.verbose)
            else:
                exit_code = runner.run_unit_tests(args.verbose, args.parallel)
        elif args.integration:
            if args.coverage:
                exit_code = runner.run_with_coverage("integration", args.verbose)
            else:
                exit_code = runner.run_integration_tests(args.verbose, args.parallel)
        elif args.performance:
            exit_code = runner.run_performance_tests(args.verbose)
        elif args.smoke:
            exit_code = runner.run_smoke_tests(args.verbose)
        elif args.security:
            exit_code = runner.run_security_tests(args.verbose)
        elif args.custom:
            exit_code = runner.run_custom_tests(args.custom, args.verbose)
        elif args.all or args.coverage:
            if args.coverage:
                exit_code = runner.run_with_coverage("all", args.verbose)
            else:
                exit_code = runner.run_all_tests(args.verbose, args.parallel)
        else:
            # Default: run unit tests
            exit_code = runner.run_unit_tests(args.verbose, args.parallel)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if exit_code == 0:
            print(f"\n✅ Tests completed successfully in {duration:.2f}s")
        else:
            print(f"\n❌ Tests failed in {duration:.2f}s")
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 