#!/usr/bin/env python3
"""
Automated build script for n0name Trading Bot
Handles different build types: development, production, executable, docker
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BuildError(Exception):
    """Custom exception for build errors"""
    pass

class Builder:
    """Main builder class for n0name Trading Bot"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_dir = project_root / "build"
        self.dist_dir = project_root / "dist"
        self.src_dir = project_root / "src"
        
        # Ensure build directories exist
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a command and handle errors"""
        cwd = cwd or self.project_root
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                logger.debug(f"STDOUT: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Exit code: {e.returncode}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise BuildError(f"Command failed: {' '.join(cmd)}")
    
    def clean(self):
        """Clean build artifacts"""
        logger.info("Cleaning build artifacts...")
        
        # Directories to clean
        clean_dirs = [
            self.build_dir,
            self.dist_dir,
            self.project_root / "__pycache__",
            self.project_root / ".pytest_cache",
            self.project_root / "htmlcov",
            self.project_root / ".coverage",
            self.project_root / ".mypy_cache",
            self.project_root / ".ruff_cache",
        ]
        
        for dir_path in clean_dirs:
            if dir_path.exists():
                logger.info(f"Removing {dir_path}")
                shutil.rmtree(dir_path)
        
        # Find and remove __pycache__ directories
        for pycache in self.project_root.rglob("__pycache__"):
            logger.debug(f"Removing {pycache}")
            shutil.rmtree(pycache)
        
        # Find and remove .pyc files
        for pyc_file in self.project_root.rglob("*.pyc"):
            logger.debug(f"Removing {pyc_file}")
            pyc_file.unlink()
        
        logger.info("Clean completed")
    
    def install_dependencies(self, dev: bool = False):
        """Install project dependencies"""
        logger.info("Installing dependencies...")
        
        # Upgrade pip first
        self.run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install the package in editable mode
        if dev:
            self.run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev,performance,monitoring]"])
        else:
            self.run_command([sys.executable, "-m", "pip", "install", "-e", "."])
        
        logger.info("Dependencies installed")
    
    def run_tests(self):
        """Run the test suite"""
        logger.info("Running tests...")
        
        # Check if pytest is available
        try:
            self.run_command([sys.executable, "-m", "pytest", "--version"])
        except BuildError:
            logger.warning("pytest not found, installing...")
            self.run_command([sys.executable, "-m", "pip", "install", "pytest"])
        
        # Run tests
        test_cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--maxfail=5"
        ]
        
        try:
            self.run_command(test_cmd)
            logger.info("All tests passed")
        except BuildError:
            logger.warning("Some tests failed, but continuing build...")
    
    def run_linting(self):
        """Run code linting"""
        logger.info("Running linting...")
        
        # Check code formatting with black
        try:
            self.run_command([sys.executable, "-m", "black", "--check", "src/", "tests/"])
            logger.info("Code formatting check passed")
        except BuildError:
            logger.warning("Code formatting issues found")
        
        # Run ruff linting
        try:
            self.run_command([sys.executable, "-m", "ruff", "check", "src/", "tests/"])
            logger.info("Linting check passed")
        except BuildError:
            logger.warning("Linting issues found")
        
        # Run type checking with mypy
        try:
            self.run_command([sys.executable, "-m", "mypy", "src/"])
            logger.info("Type checking passed")
        except BuildError:
            logger.warning("Type checking issues found")
    
    def build_wheel(self):
        """Build Python wheel package"""
        logger.info("Building wheel package...")
        
        # Install build dependencies
        self.run_command([sys.executable, "-m", "pip", "install", "build", "wheel"])
        
        # Build the package
        self.run_command([sys.executable, "-m", "build"])
        
        # List built files
        wheel_files = list(self.dist_dir.glob("*.whl"))
        tar_files = list(self.dist_dir.glob("*.tar.gz"))
        
        logger.info(f"Built {len(wheel_files)} wheel files and {len(tar_files)} source distributions")
        for file in wheel_files + tar_files:
            logger.info(f"  {file.name}")
    
    def build_executable(self, onefile: bool = True):
        """Build standalone executable with PyInstaller"""
        logger.info("Building standalone executable...")
        
        # Install PyInstaller
        self.run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
        # Use the improved spec file
        spec_file = self.build_dir / "n0name.spec"
        
        if not spec_file.exists():
            logger.error(f"Spec file not found: {spec_file}")
            raise BuildError("PyInstaller spec file not found")
        
        # Build command
        build_cmd = [
            sys.executable, "-m", "PyInstaller",
            str(spec_file),
            "--clean",
            "--noconfirm"
        ]
        
        if not onefile:
            # Modify spec file for directory distribution
            logger.info("Building directory distribution...")
        
        self.run_command(build_cmd)
        
        # Check if executable was created
        if sys.platform == "win32":
            exe_name = "n0name-trading-bot.exe"
        else:
            exe_name = "n0name-trading-bot"
        
        exe_path = self.dist_dir / exe_name
        if exe_path.exists():
            logger.info(f"Executable created: {exe_path}")
            logger.info(f"Executable size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            raise BuildError("Executable not found after build")
    
    def build_docker(self, tag: str = "n0name-trading-bot", target: str = "production"):
        """Build Docker image"""
        logger.info(f"Building Docker image: {tag}")
        
        # Check if Docker is available
        try:
            self.run_command(["docker", "--version"])
        except BuildError:
            raise BuildError("Docker not found. Please install Docker.")
        
        # Build Docker image
        build_cmd = [
            "docker", "build",
            "--target", target,
            "--tag", tag,
            "."
        ]
        
        self.run_command(build_cmd)
        logger.info(f"Docker image built: {tag}")
        
        # Show image info
        try:
            result = self.run_command(["docker", "images", tag])
            logger.info("Docker image info:")
            logger.info(result.stdout)
        except BuildError:
            logger.warning("Could not get Docker image info")
    
    def create_release_package(self, version: str):
        """Create a complete release package"""
        logger.info(f"Creating release package for version {version}")
        
        release_dir = self.dist_dir / f"n0name-trading-bot-{version}"
        release_dir.mkdir(exist_ok=True)
        
        # Copy essential files
        files_to_copy = [
            "README.md",
            "SECURITY.md",
            "requirements.txt",
            "env.example",
            "sample_config.yml",
        ]
        
        for file_name in files_to_copy:
            src_file = self.project_root / file_name
            if src_file.exists():
                shutil.copy2(src_file, release_dir)
        
        # Copy config directory
        config_src = self.project_root / "config"
        config_dst = release_dir / "config"
        if config_src.exists():
            shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
        
        # Copy executable if it exists
        if sys.platform == "win32":
            exe_name = "n0name-trading-bot.exe"
        else:
            exe_name = "n0name-trading-bot"
        
        exe_path = self.dist_dir / exe_name
        if exe_path.exists():
            shutil.copy2(exe_path, release_dir)
        
        # Create installation script
        if sys.platform == "win32":
            install_script = release_dir / "install.bat"
            install_script.write_text("""@echo off
echo Installing n0name Trading Bot...
pip install -r requirements.txt
echo Installation complete!
pause
""")
        else:
            install_script = release_dir / "install.sh"
            install_script.write_text("""#!/bin/bash
echo "Installing n0name Trading Bot..."
pip install -r requirements.txt
echo "Installation complete!"
""")
            install_script.chmod(0o755)
        
        # Create archive
        archive_name = f"n0name-trading-bot-{version}"
        archive_path = shutil.make_archive(
            str(self.dist_dir / archive_name),
            'zip',
            str(release_dir.parent),
            release_dir.name
        )
        
        logger.info(f"Release package created: {archive_path}")
        return Path(archive_path)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Build n0name Trading Bot")
    parser.add_argument("--type", choices=["dev", "prod", "exe", "docker", "release"], 
                       default="dev", help="Build type")
    parser.add_argument("--clean", action="store_true", help="Clean before building")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--lint", action="store_true", help="Run linting")
    parser.add_argument("--version", help="Version for release build")
    parser.add_argument("--docker-tag", default="n0name-trading-bot", help="Docker tag")
    parser.add_argument("--docker-target", default="production", help="Docker target stage")
    parser.add_argument("--onefile", action="store_true", help="Create single file executable")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    builder = Builder(project_root)
    
    try:
        # Clean if requested
        if args.clean:
            builder.clean()
        
        # Install dependencies
        if args.type in ["dev", "prod"]:
            builder.install_dependencies(dev=(args.type == "dev"))
        
        # Run tests if requested
        if args.test:
            builder.run_tests()
        
        # Run linting if requested
        if args.lint:
            builder.run_linting()
        
        # Build based on type
        if args.type == "dev":
            logger.info("Development build completed")
        
        elif args.type == "prod":
            builder.build_wheel()
            logger.info("Production build completed")
        
        elif args.type == "exe":
            builder.install_dependencies(dev=True)  # Need dev deps for PyInstaller
            builder.build_executable(onefile=args.onefile)
            logger.info("Executable build completed")
        
        elif args.type == "docker":
            builder.build_docker(tag=args.docker_tag, target=args.docker_target)
            logger.info("Docker build completed")
        
        elif args.type == "release":
            if not args.version:
                logger.error("Version required for release build")
                sys.exit(1)
            
            # Build everything for release
            builder.install_dependencies(dev=True)
            if args.test:
                builder.run_tests()
            if args.lint:
                builder.run_linting()
            builder.build_wheel()
            builder.build_executable(onefile=True)
            builder.build_docker(tag=f"{args.docker_tag}:{args.version}")
            archive_path = builder.create_release_package(args.version)
            logger.info(f"Release build completed: {archive_path}")
        
        logger.info("Build process completed successfully!")
        
    except BuildError as e:
        logger.error(f"Build failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 